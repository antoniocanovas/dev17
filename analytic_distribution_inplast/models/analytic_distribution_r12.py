# -*- coding: utf-8 -*-
# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
#
# R12: Distribución de amortizaciones de maquinaria y utillajes entre productos base.
#
# Objetivo:
#   Crear una línea analítica de coste por producto tapón (producto base) a
#   partir de las amortizaciones mensuales contabilizadas para:
#     - Maquinaria  (model_id.account_asset_id.code = '2300000')
#     - Utillajes   (model_id.account_asset_id.code = '24000000')
#
# ─── MAQUINARIA ───────────────────────────────────────────────────────────────
#   Cada activo de maquinaria tiene asignado un mrp.workcenter (workcenter_id).
#   Se buscan las mrp.workorder ejecutadas (state='done') en el periodo para
#   ese workcenter.
#
#   coste_hora = amortización_activo / horas_totales
#   apunte por producto base = horas_producto × coste_hora
#
#   Si no hay workorders en el periodo, FALLBACK:
#   Se buscan los productos fabricables en las operaciones de las BoM que usan
#   ese workcenter o cualquiera de sus máquinas alternativas
#   (alternative_workcenter_ids). El coste se reparte equitativamente.
#
# ─── UTILLAJES (MOLDES) ───────────────────────────────────────────────────────
#   Cada activo de utillaje tiene asignado un maintenance.equipment (equipment_id).
#   Se buscan las mrp.production finalizadas en el periodo donde
#   mrp_tool_id.pnt_tool_id == equipment_id.
#   Si alguna MO de un packing no tiene mrp_tool_id, se avisa por log.
#
#   coste por producto base proporcional a qty_producida × pnt_parent_qty.
#
#   Si no hay MOs en el periodo, FALLBACK:
#   Se buscan los product.template que tienen el utillaje asignado en
#   mrp_tool_ids.pnt_tool_id. El coste se reparte equitativamente.
#
# Validaciones / avisos por log:
#   - Workorder sin workcenter_id.
#   - MO de packing sin mrp_tool_id configurado.
#   - Activo de maquinaria sin workcenter_id.
#   - Activo de utillaje sin equipment_id.
from odoo import models
import logging
_logger = logging.getLogger(__name__)

MACHINERY_ACCOUNT_CODE = '2130000'
TOOL_ACCOUNT_CODE = '21400000'


class AnalyticDistribution(models.Model):
    _inherit = 'analytic.distribution'

    def compute_r12(self, li):
        """Distribuye las amortizaciones mensuales de maquinaria y utillajes
        entre los productos base (tapones) en función de las horas de máquina
        consumidas (maquinaria) o las unidades fabricadas (utillajes).

        Parámetros:
            li  (analytic.distribution.line): línea con el template R12 que
                contiene el balance contable (total amortizaciones del periodo).
        """
        for rec in self:
            method = 'R12'
            balance = li.balance
            _logger.warning("[%s] Iniciando cálculo. balance=%.2f", method, balance)
            if not balance:
                _logger.warning("[%s] SALIDA: balance es 0 o nulo.", method)
                return

            date_from = rec.date_from
            date_to = rec.date_to
            # account.move.date es Date, rec.date_from/to son Datetime → convertir
            date_from_d = date_from.date() if hasattr(date_from, 'date') else date_from
            date_to_d = date_to.date() if hasattr(date_to, 'date') else date_to
            _logger.warning("[%s] Periodo: %s → %s", method, date_from_d, date_to_d)

            # Campos analíticos comunes
            product_field_id = self.env.company.product_field_id.name
            fixed_variable_field_id = self.env.company.fixed_variable_field_id.name
            department_field_id = self.env.company.department_field_id.name
            mrp_dept = self.env.company.analytic_mrp_department_id
            variable_account = self.env.company.analytic_variable_account_id

            ctx = {
                'rec': rec,
                'li': li,
                'method': method,
                'date_from': date_from,
                'date_to': date_to,
                'date_from_d': date_from_d,
                'date_to_d': date_to_d,
                'product_field_id': product_field_id,
                'fixed_variable_field_id': fixed_variable_field_id,
                'department_field_id': department_field_id,
                'mrp_dept': mrp_dept,
                'variable_account': variable_account,
            }

            # ── Maquinaria ──────────────────────────────────────────────────
            machinery_assets = self.env['account.asset'].search([
                ('model_id.account_asset_id.code', '=', MACHINERY_ACCOUNT_CODE),
            ])
            _logger.warning("[%s] Activos maquinaria encontrados: %d", method, len(machinery_assets))
            for asset in machinery_assets:
                self._r12_process_machinery_asset(asset, ctx)

            # ── Utillajes ────────────────────────────────────────────────────
            tool_assets = self.env['account.asset'].search([
                ('model_id.account_asset_id.code', '=', TOOL_ACCOUNT_CODE),
            ])
            _logger.warning("[%s] Activos utillaje encontrados: %d", method, len(tool_assets))
            for asset in tool_assets:
                self._r12_process_tool_asset(asset, ctx)

    # =========================================================================
    # Helpers internos
    # =========================================================================

    def _r12_get_asset_amort(self, asset, date_from_d, date_to_d):
        """Devuelve el importe total de amortización contabilizada para el
        activo en el periodo (suma de débitos de los asientos de amortización
        confirmados)."""
        amort_moves = self.env['account.move'].search([
            ('asset_id', '=', asset.id),
            ('date', '>=', date_from_d),
            ('date', '<=', date_to_d),
            ('state', '=', 'posted'),
        ])
        return sum(line.debit for move in amort_moves for line in move.line_ids if line.debit > 0)

    def _r12_create_analytic_line(self, ctx, base_tmpl, wo_or_mo_product, cost, note):
        """Crea un apunte analítico para el producto base indicado."""
        rec = ctx['rec']
        li = ctx['li']
        analytic_account = self.check_or_create_analytic_account(base_tmpl)
        # product_id necesita product.product, no product.template
        product_pp = (
            wo_or_mo_product
            if wo_or_mo_product and wo_or_mo_product._name == 'product.product'
            else base_tmpl.product_variant_ids[:1]
        )
        self.env['account.analytic.line'].create({
            'product_id': product_pp.id if product_pp else False,
            'name': f"{li.template_id.name} - {rec.name} | {base_tmpl.name}",
            'amount': -abs(cost),
            ctx['product_field_id']: analytic_account.id,
            ctx['fixed_variable_field_id']: ctx['variable_account'].id,
            'analytic_distribution_id': rec.id,
            'analytic_distribution_template_id': li.template_id.id,
            'analytic_distribution_note': note,
        })

    # -------------------------------------------------------------------------
    # Maquinaria
    # -------------------------------------------------------------------------

    def _r12_process_machinery_asset(self, asset, ctx):
        method = ctx['method']
        amort_amount = self._r12_get_asset_amort(asset, ctx['date_from_d'], ctx['date_to_d'])
        _logger.warning("[%s] Activo maquinaria '%s': amortización=%.2f", method, asset.name, amort_amount)
        if not amort_amount:
            return

        workcenter = asset.workcenter_id
        if not workcenter:
            _logger.warning("[%s] Activo '%s' sin workcenter_id configurado, ignorado.", method, asset.name)
            return

        # 1. Buscar workorders finalizados para este workcenter en el periodo
        workorders = self.env['mrp.workorder'].search([
            ('workcenter_id', '=', workcenter.id),
            ('date_start', '>=', ctx['date_from']),
            ('date_start', '<=', ctx['date_to']),
            ('state', '=', 'done'),
        ])
        _logger.warning("[%s]   '%s' → workorders en periodo: %d", method, workcenter.name, len(workorders))

        if not workorders:
            _logger.warning("[%s]   Sin workorders: aplicando FALLBACK por BoM.", method)
            self._r12_machinery_fallback(asset, amort_amount, ctx)
            return

        # 2. Validar workorders sin workcenter (aviso de datos)
        for wo in workorders:
            if not wo.workcenter_id:
                _logger.warning(
                    "[%s]   La orden de producción '%s' no tiene máquina asociada (workcenter_id).",
                    method, wo.production_id.name if wo.production_id else wo.name
                )

        # 3. Acumular minutos por producto base
        product_minutes = {}
        for wo in workorders:
            packing = wo.product_id
            if packing.pnt_product_type == 'packing':
                base_tmpl = packing.pnt_parent_id
            else:
                base_tmpl = packing.product_tmpl_id
            if not base_tmpl:
                continue
            product_minutes[base_tmpl] = product_minutes.get(base_tmpl, 0.0) + wo.duration

        total_minutes = sum(product_minutes.values())
        total_hours = total_minutes / 60.0
        if total_hours <= 0:
            _logger.warning("[%s]   Total horas = 0 para '%s', ignorado.", method, asset.name)
            return

        cost_per_hour = amort_amount / total_hours
        _logger.warning("[%s]   Total horas: %.2f | Coste/hora: %.4f", method, total_hours, cost_per_hour)

        # 4. Crear apuntes analíticos
        for base_tmpl, minutes in product_minutes.items():
            hours = minutes / 60.0
            cost = hours * cost_per_hour
            proportion_pct = (hours / total_hours) * 100
            note = (
                f"Informe: {method} — Maquinaria\n"
                f"Activo: {asset.name}\n"
                f"Máquina (workcenter): {workcenter.name}\n"
                f"Producto base: {base_tmpl.name}\n"
                f"─── Cálculo ───\n"
                f"  Amortización activo en periodo: {amort_amount:.2f}\n"
                f"  Horas producto: {hours:.2f} h / {total_hours:.2f} h total\n"
                f"  Proporción: {proportion_pct:.4f}%\n"
                f"  Coste/hora: {cost_per_hour:.4f} €/h\n"
                f"  Coste asignado = {hours:.2f} × {cost_per_hour:.4f} = {cost:.2f}"
            )
            self._r12_create_analytic_line(ctx, base_tmpl, None, cost, note)
            _logger.warning("[%s]     %s → %.2f h → %.2f€", method, base_tmpl.name, hours, cost)

    def _r12_machinery_fallback(self, asset, amort_amount, ctx):
        """Fallback maquinaria: no hay workorders → buscar productos fabricables
        en las operaciones de BoM para este workcenter o sus alternativas.
        El coste se reparte equitativamente entre todos los productos encontrados."""
        method = ctx['method']
        workcenter = asset.workcenter_id
        all_wcs = workcenter | workcenter.alternative_workcenter_ids
        _logger.warning("[%s]   FALLBACK: buscando BoM operations para %d workcenter(s).",
                        method, len(all_wcs))

        bom_operations = self.env['mrp.routing.workcenter'].search([
            ('workcenter_id', 'in', all_wcs.ids),
        ])
        base_tmpls = bom_operations.mapped('bom_id.product_tmpl_id')

        # Si el producto de la BoM es un packing, subir al producto base
        base_set = set()
        for tmpl in base_tmpls:
            if tmpl.pnt_product_type == 'packing' and tmpl.pnt_parent_id:
                base_set.add(tmpl.pnt_parent_id)
            else:
                base_set.add(tmpl)

        if not base_set:
            _logger.warning("[%s]   FALLBACK: sin productos en BoM para '%s', ignorado.",
                            method, asset.name)
            return

        cost_each = amort_amount / len(base_set)
        _logger.warning("[%s]   FALLBACK: %d productos | coste/producto=%.2f",
                        method, len(base_set), cost_each)

        for base_tmpl in base_set:
            note = (
                f"Informe: {method} — Maquinaria (FALLBACK sin producción)\n"
                f"Activo: {asset.name}\n"
                f"Máquina (workcenter): {workcenter.name}\n"
                f"Producto base: {base_tmpl.name}\n"
                f"─── Cálculo ───\n"
                f"  Amortización activo en periodo: {amort_amount:.2f}\n"
                f"  Sin workorders → reparto equitativo entre {len(base_set)} productos.\n"
                f"  Coste asignado = {amort_amount:.2f} / {len(base_set)} = {cost_each:.2f}"
            )
            self._r12_create_analytic_line(ctx, base_tmpl, None, cost_each, note)

    # -------------------------------------------------------------------------
    # Utillajes (moldes)
    # -------------------------------------------------------------------------

    def _r12_process_tool_asset(self, asset, ctx):
        method = ctx['method']
        amort_amount = self._r12_get_asset_amort(asset, ctx['date_from_d'], ctx['date_to_d'])
        _logger.warning("[%s] Activo utillaje '%s': amortización=%.2f", method, asset.name, amort_amount)
        if not amort_amount:
            return

        equipment = asset.equipment_id
        if not equipment:
            _logger.warning("[%s] Activo '%s' sin equipment_id configurado, ignorado.", method, asset.name)
            return

        # 1. Buscar configuraciones de herramienta que apunten a este equipo
        tool_configs = self.env['mrp.product.tool'].search([
            ('pnt_tool_id', '=', equipment.id),
        ])

        # 2. Buscar MOs finalizadas en el periodo que usen estas configuraciones
        productions = self.env['mrp.production'].search([
            ('mrp_tool_id', 'in', tool_configs.ids),
            ('date_finished', '>=', ctx['date_from']),
            ('date_finished', '<=', ctx['date_to']),
            ('state', '=', 'done'),
        ])
        _logger.warning("[%s]   '%s' → MOs en periodo: %d", method, equipment.name, len(productions))

        if not productions:
            _logger.warning("[%s]   Sin MOs: aplicando FALLBACK por configuración de producto.", method)
            self._r12_tool_fallback(asset, equipment, amort_amount, ctx)
            return

        # 3. Validar MOs de packing sin molde configurado
        all_packing_mos = self.env['mrp.production'].search([
            ('product_id.pnt_product_type', '=', 'packing'),
            ('date_finished', '>=', ctx['date_from']),
            ('date_finished', '<=', ctx['date_to']),
            ('state', '=', 'done'),
        ])
        for mo in all_packing_mos:
            if not mo.mrp_tool_id:
                _logger.warning(
                    "[%s]   La orden de fabricación '%s' no tiene molde configurado.",
                    method, mo.name
                )

        # 4. Acumular unidades de producto base por MO
        qty_per_base = {}
        for mo in productions:
            packing = mo.product_id
            if packing.pnt_product_type == 'packing':
                base_tmpl = packing.pnt_parent_id
            else:
                base_tmpl = packing.product_tmpl_id
            if not base_tmpl:
                continue
            base_qty = mo.qty_produced * (packing.pnt_parent_qty or 1.0)
            qty_per_base[base_tmpl] = qty_per_base.get(base_tmpl, 0.0) + base_qty

        total_qty = sum(qty_per_base.values())
        if total_qty <= 0:
            _logger.warning("[%s]   Total unidades = 0 para '%s', ignorado.", method, asset.name)
            return

        _logger.warning("[%s]   Total unidades base: %.2f", method, total_qty)

        # 5. Crear apuntes analíticos proporcionales a las unidades fabricadas
        for base_tmpl, qty in qty_per_base.items():
            proportion = qty / total_qty
            cost = amort_amount * proportion
            proportion_pct = proportion * 100
            note = (
                f"Informe: {method} — Utillaje (molde)\n"
                f"Activo: {asset.name}\n"
                f"Utillaje (equipment): {equipment.name}\n"
                f"Producto base: {base_tmpl.name}\n"
                f"─── Cálculo ───\n"
                f"  Amortización activo en periodo: {amort_amount:.2f}\n"
                f"  Unidades base fabricadas (producto): {qty:.2f}\n"
                f"  Unidades base fabricadas (total): {total_qty:.2f}\n"
                f"  Proporción: {proportion_pct:.4f}%\n"
                f"  Coste asignado = {amort_amount:.2f} × {proportion_pct:.4f}% = {cost:.2f}"
            )
            self._r12_create_analytic_line(ctx, base_tmpl, None, cost, note)
            _logger.warning("[%s]     %s → %.2f u → %.2f€", method, base_tmpl.name, qty, cost)

    def _r12_tool_fallback(self, asset, equipment, amort_amount, ctx):
        """Fallback utillaje: no hay MOs → buscar product.template que tienen
        este utillaje asignado en mrp_tool_ids.pnt_tool_id.
        El coste se reparte equitativamente."""
        method = ctx['method']

        tool_product_records = self.env['mrp.product.tool'].search([
            ('pnt_tool_id', '=', equipment.id),
        ])
        base_tmpls = list(set(tool_product_records.mapped('product_tmpl_id')))

        if not base_tmpls:
            _logger.warning("[%s]   FALLBACK: sin productos con utillaje '%s', ignorado.",
                            method, equipment.name)
            return

        cost_each = amort_amount / len(base_tmpls)
        _logger.warning("[%s]   FALLBACK: %d productos | coste/producto=%.2f",
                        method, len(base_tmpls), cost_each)

        for base_tmpl in base_tmpls:
            note = (
                f"Informe: {method} — Utillaje (FALLBACK sin producción)\n"
                f"Activo: {asset.name}\n"
                f"Utillaje (equipment): {equipment.name}\n"
                f"Producto base: {base_tmpl.name}\n"
                f"─── Cálculo ───\n"
                f"  Amortización activo en periodo: {amort_amount:.2f}\n"
                f"  Sin MOs → reparto equitativo entre {len(base_tmpls)} productos.\n"
                f"  Coste asignado = {amort_amount:.2f} / {len(base_tmpls)} = {cost_each:.2f}"
            )
            self._r12_create_analytic_line(ctx, base_tmpl, None, cost_each, note)

    # =========================================================================
    # R12 LEGACY: misma lógica pero usando mrp.production.legacy
    # =========================================================================
    #
    # mrp.production.legacy expone:
    #   name         → product.template (packing)
    #   product_qty  → unidades fabricadas
    #   parent_id    → product.template base (related: name.pnt_parent_id)
    #   date         → fecha (Date)
    #   machine_id   → account.analytic.account (la máquina/workcenter)
    #   time         → horas empleadas (Float)
    #
    # Matching activo → legacy:
    #   Maquinaria : asset.workcenter_id → mrp.workcenter
    #                → account.analytic.account (workcenter_id = workcenter)
    #                → legacy.machine_id
    #   Utillaje   : asset.equipment_id → maintenance.equipment
    #                → mrp.product.tool (pnt_tool_id = equipment)
    #                → legacy.name (packing product del tool)
    # =========================================================================

    def compute_r12_legacy(self, li):
        """Versión legacy de compute_r12: usa mrp.production.legacy en lugar de
        mrp.production / mrp.workorder para distribuir amortizaciones de
        maquinaria y utillajes entre productos base.

        Parámetros:
            li  (analytic.distribution.line): línea con el template R12_LEGACY.
        """
        for rec in self:
            method = 'R12_LEGACY'
            balance = li.balance
            _logger.warning("[%s] Iniciando cálculo. balance=%.2f", method, balance)
            if not balance:
                _logger.warning("[%s] SALIDA: balance es 0 o nulo.", method)
                return

            date_from = rec.date_from
            date_to = rec.date_to
            date_from_d = date_from.date() if hasattr(date_from, 'date') else date_from
            date_to_d = date_to.date() if hasattr(date_to, 'date') else date_to
            _logger.warning("[%s] Periodo: %s → %s", method, date_from_d, date_to_d)

            product_field_id = self.env.company.product_field_id.name
            fixed_variable_field_id = self.env.company.fixed_variable_field_id.name
            department_field_id = self.env.company.department_field_id.name
            mrp_dept = self.env.company.analytic_mrp_department_id
            variable_account = self.env.company.analytic_variable_account_id

            ctx = {
                'rec': rec,
                'li': li,
                'method': method,
                'date_from': date_from,
                'date_to': date_to,
                'date_from_d': date_from_d,
                'date_to_d': date_to_d,
                'product_field_id': product_field_id,
                'fixed_variable_field_id': fixed_variable_field_id,
                'department_field_id': department_field_id,
                'mrp_dept': mrp_dept,
                'variable_account': variable_account,
            }

            # ── Maquinaria ──────────────────────────────────────────────────
            machinery_assets = self.env['account.asset'].search([
                ('model_id.account_asset_id.code', '=', MACHINERY_ACCOUNT_CODE),
            ])
            _logger.warning("[%s] Activos maquinaria encontrados: %d", method, len(machinery_assets))
            for asset in machinery_assets:
                self._r12_legacy_process_machinery_asset(asset, ctx)

            # ── Utillajes ────────────────────────────────────────────────────
            tool_assets = self.env['account.asset'].search([
                ('model_id.account_asset_id.code', '=', TOOL_ACCOUNT_CODE),
            ])
            _logger.warning("[%s] Activos utillaje encontrados: %d", method, len(tool_assets))
            for asset in tool_assets:
                self._r12_legacy_process_tool_asset(asset, ctx)

    def _r12_legacy_process_machinery_asset(self, asset, ctx):
        """Distribuye la amortización de un activo de maquinaria entre productos
        base usando las horas registradas en mrp.production.legacy."""
        method = ctx['method']
        amort_amount = self._r12_get_asset_amort(asset, ctx['date_from_d'], ctx['date_to_d'])
        _logger.warning("[%s] Activo maquinaria '%s': amortización=%.2f", method, asset.name, amort_amount)
        if not amort_amount:
            return

        workcenter = asset.workcenter_id
        if not workcenter:
            _logger.warning("[%s] Activo '%s' sin workcenter_id configurado, ignorado.", method, asset.name)
            return

        # Cuenta analítica que representa este workcenter
        analytic_acct = self.env['account.analytic.account'].search([
            ('workcenter_id', '=', workcenter.id),
        ], limit=1)
        if not analytic_acct:
            _logger.warning(
                "[%s] Workcenter '%s' sin cuenta analítica (account.analytic.account.workcenter_id), ignorado.",
                method, workcenter.name,
            )
            return

        # Registros legacy de esta máquina en el periodo
        legacy_records = self.env['mrp.production.legacy'].search([
            ('machine_id', '=', analytic_acct.id),
            ('date', '>=', ctx['date_from_d']),
            ('date', '<=', ctx['date_to_d']),
        ])
        _logger.warning("[%s]   '%s' → registros legacy en periodo: %d",
                        method, workcenter.name, len(legacy_records))

        if not legacy_records:
            _logger.warning("[%s]   Sin registros legacy: aplicando FALLBACK por BoM.", method)
            self._r12_machinery_fallback(asset, amort_amount, ctx)
            return

        # Acumular horas por producto base
        product_hours = {}
        for lr in legacy_records:
            base_tmpl = lr.parent_id or lr.name
            if not base_tmpl:
                continue
            product_hours[base_tmpl] = product_hours.get(base_tmpl, 0.0) + lr.time

        total_hours = sum(product_hours.values())
        if total_hours <= 0:
            _logger.warning("[%s]   Total horas = 0 para '%s', ignorado.", method, asset.name)
            return

        cost_per_hour = amort_amount / total_hours
        _logger.warning("[%s]   Total horas: %.2f | Coste/hora: %.4f", method, total_hours, cost_per_hour)

        for base_tmpl, hours in product_hours.items():
            cost = hours * cost_per_hour
            proportion_pct = (hours / total_hours) * 100
            note = (
                f"Informe: {method} — Maquinaria (Legacy)\n"
                f"Activo: {asset.name}\n"
                f"Máquina (workcenter): {workcenter.name} | Cuenta analítica: {analytic_acct.name}\n"
                f"Producto base: {base_tmpl.name}\n"
                f"─── Cálculo ───\n"
                f"  Amortización activo en periodo: {amort_amount:.2f}\n"
                f"  Horas producto: {hours:.2f} h / {total_hours:.2f} h total\n"
                f"  Proporción: {proportion_pct:.4f}%\n"
                f"  Coste/hora: {cost_per_hour:.4f} €/h\n"
                f"  Coste asignado = {hours:.2f} × {cost_per_hour:.4f} = {cost:.2f}"
            )
            self._r12_create_analytic_line(ctx, base_tmpl, None, cost, note)
            _logger.warning("[%s]     %s → %.2f h → %.2f€", method, base_tmpl.name, hours, cost)

    def _r12_legacy_process_tool_asset(self, asset, ctx):
        """Distribuye la amortización de un activo de utillaje entre productos
        base usando las cantidades registradas en mrp.production.legacy para los
        productos que tienen ese utillaje configurado."""
        method = ctx['method']
        amort_amount = self._r12_get_asset_amort(asset, ctx['date_from_d'], ctx['date_to_d'])
        _logger.warning("[%s] Activo utillaje '%s': amortización=%.2f", method, asset.name, amort_amount)
        if not amort_amount:
            return

        equipment = asset.equipment_id
        if not equipment:
            _logger.warning("[%s] Activo '%s' sin equipment_id configurado, ignorado.", method, asset.name)
            return

        # Productos packing que usan este utillaje
        tool_configs = self.env['mrp.product.tool'].search([
            ('pnt_tool_id', '=', equipment.id),
        ])
        if not tool_configs:
            _logger.warning("[%s] Equipo '%s' sin configuraciones mrp.product.tool, ignorado.",
                            method, equipment.name)
            return

        packing_tmpls = tool_configs.mapped('product_tmpl_id')

        # Registros legacy del periodo donde el producto packing usa este utillaje
        legacy_records = self.env['mrp.production.legacy'].search([
            ('name', 'in', packing_tmpls.ids),
            ('date', '>=', ctx['date_from_d']),
            ('date', '<=', ctx['date_to_d']),
        ])
        _logger.warning("[%s]   '%s' → registros legacy en periodo: %d",
                        method, equipment.name, len(legacy_records))

        if not legacy_records:
            _logger.warning("[%s]   Sin registros legacy: aplicando FALLBACK por configuración de producto.", method)
            self._r12_tool_fallback(asset, equipment, amort_amount, ctx)
            return

        # Acumular unidades de producto base ponderadas por pnt_parent_qty
        qty_per_base = {}
        for lr in legacy_records:
            packing_tmpl = lr.name
            base_tmpl = lr.parent_id or packing_tmpl
            if not base_tmpl:
                continue
            pnt_parent_qty = packing_tmpl.pnt_parent_qty or 1.0
            base_qty = lr.product_qty * pnt_parent_qty
            qty_per_base[base_tmpl] = qty_per_base.get(base_tmpl, 0.0) + base_qty

        total_qty = sum(qty_per_base.values())
        if total_qty <= 0:
            _logger.warning("[%s]   Total unidades = 0 para '%s', ignorado.", method, asset.name)
            return

        _logger.warning("[%s]   Total unidades base: %.2f", method, total_qty)

        for base_tmpl, qty in qty_per_base.items():
            proportion = qty / total_qty
            cost = amort_amount * proportion
            proportion_pct = proportion * 100
            note = (
                f"Informe: {method} — Utillaje/molde (Legacy)\n"
                f"Activo: {asset.name}\n"
                f"Utillaje (equipment): {equipment.name}\n"
                f"Producto base: {base_tmpl.name}\n"
                f"─── Cálculo ───\n"
                f"  Amortización activo en periodo: {amort_amount:.2f}\n"
                f"  Unidades base fabricadas (producto): {qty:.2f}\n"
                f"  Unidades base fabricadas (total): {total_qty:.2f}\n"
                f"  Proporción: {proportion_pct:.4f}%\n"
                f"  Coste asignado = {amort_amount:.2f} × {proportion_pct:.4f}% = {cost:.2f}"
            )
            self._r12_create_analytic_line(ctx, base_tmpl, None, cost, note)
            _logger.warning("[%s]     %s → %.2f u → %.2f€", method, base_tmpl.name, qty, cost)
