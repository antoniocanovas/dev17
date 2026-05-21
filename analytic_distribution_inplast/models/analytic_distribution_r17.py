# -*- coding: utf-8 -*-
# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
#
# R17: Distribución de costes de máquinas, moldes y otros entre productos base.
#
# Objetivo:
#   Repartir el balance del template entre productos base (pnt_parent_id)
#   dividiendo el importe en tres componentes extraídos de account.move.line:
#
#   · coste_maquinas: porción proporcional de move.lines cuya analytic_distribution
#     contiene cuentas del plan company_id.analytic_machine_plan_id.
#   · coste_moldes: porción proporcional de move.lines cuya analytic_distribution
#     contiene cuentas del plan company_id.analytic_equipment_plan_id.
#   · coste_otros: li.balance − coste_maquinas − coste_moldes.
#
# ─── DISTRIBUCIÓN COSTE_MAQUINAS ─────────────────────────────────────────────
#   Tasa global: coste_maquinas_activas / horas_maquina_total
#   donde:
#     · coste_maquinas_activas: costes de cuentas de máquina cuyo workcenter_id
#       tiene mrp.workorder en el periodo (state='done').
#     · horas_maquina_total: horas totales de TODOS los mrp.workorder del periodo.
#   Para cada producto base: analytic.line = tasa × horas_producto_base.
#
#   Fallback (cuentas de máquina con costes pero sin workorders en el periodo):
#     Buscar en workcenter.tag_ids la primera etiqueta en
#     company_id.mrp_workcenter_tag_ids → agrupar todos los workcenters con esa
#     etiqueta → productos base fabricables en sus BoM (mrp.routing.workcenter)
#     → reparto equitativo.
#
# ─── DISTRIBUCIÓN COSTE_MOLDES ────────────────────────────────────────────────
#   Tasa global: coste_moldes_activos / horas_molde_total
#   donde:
#     · coste_moldes_activos: costes de cuentas de molde cuyo equipment_id
#       aparece como production.mrp_tool_id.pnt_tool_id en workorders del periodo.
#     · horas_molde_total: horas de workorders cuyas producciones tienen molde.
#   Para cada producto base (pnt_parent_id): analytic.line = tasa × horas.
#
#   Fallback (cuentas de molde sin workorders en el periodo):
#     Buscar en mrp.product.tool registros con pnt_tool_id == equipment_id cuyo
#     product_tmpl_id.pnt_product_type == 'final' → reparto equitativo.
#
# ─── DISTRIBUCIÓN COSTE_OTROS ─────────────────────────────────────────────────
#   Tasa global: coste_otros / horas_maquina_total (todos los workorders).
#   Para cada producto base: analytic.line = tasa × horas_producto_base.
#
# ─── VERSIÓN LEGACY ───────────────────────────────────────────────────────────
#   · coste_maquinas: distribuido con mrp.production.legacy
#     (machine_id → tiempo por producto base).
#   · coste_moldes: sin info de moldes en legacy → se trata como coste_otros.
#   · coste_otros + coste_moldes: distribuidos con horas legacy por producto base.
#   Fallback en ambos casos: si no hay registros legacy para una máquina → BoM.

from odoo import models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AnalyticDistribution(models.Model):
    _inherit = 'analytic.distribution'

    # =========================================================================
    # R17
    # =========================================================================

    def compute_r17(self, li):
        """Distribuye el balance entre productos base según costes de máquinas,
        moldes y otros, usando mrp.workorder del periodo como base de reparto.

        Parámetros:
            li  (analytic.distribution.line): línea con el template R17.
        """
        for rec in self:
            method = 'R17'
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

            company = self.env.company
            machine_plan = company.analytic_machine_plan_id
            equipment_plan = company.analytic_equipment_plan_id

            if not machine_plan:
                _logger.warning("[%s] No está configurado analytic_machine_plan_id.", method)
                return
            if not equipment_plan:
                _logger.warning("[%s] No está configurado analytic_equipment_plan_id.", method)
                return

            product_field_id = company.product_field_id.name
            fixed_variable_field_id = company.fixed_variable_field_id.name
            variable_account = company.analytic_variable_account_id

            ctx = {
                'rec': rec,
                'li': li,
                'method': method,
                'date_from': date_from,
                'date_to': date_to,
                'product_field_id': product_field_id,
                'fixed_variable_field_id': fixed_variable_field_id,
                'variable_account': variable_account,
                'balance': balance,
            }

            # ── 1. Obtener move.lines del template ────────────────────────────
            all_move_lines = li._get_expense_lines() | li._get_income_lines()

            # ── 2. Cuentas analíticas de cada plan ────────────────────────────
            machine_accounts = self.env['account.analytic.account'].search([
                ('plan_id', '=', machine_plan.id),
            ])
            equipment_accounts = self.env['account.analytic.account'].search([
                ('plan_id', '=', equipment_plan.id),
            ])
            machine_ids_str = {str(a.id): a for a in machine_accounts}
            equipment_ids_str = {str(a.id): a for a in equipment_accounts}

            # ── 3. Coste proporcional por cuenta analítica ────────────────────
            machine_cost_per_account = {}   # {account.analytic.account: float}
            equipment_cost_per_account = {}

            for line in all_move_lines:
                analytic_dist = line.analytic_distribution or {}
                line_balance = line.balance
                for str_id, pct in analytic_dist.items():
                    portion = line_balance * pct / 100.0
                    if str_id in machine_ids_str:
                        acct = machine_ids_str[str_id]
                        machine_cost_per_account[acct] = (
                            machine_cost_per_account.get(acct, 0.0) + portion
                        )
                    elif str_id in equipment_ids_str:
                        acct = equipment_ids_str[str_id]
                        equipment_cost_per_account[acct] = (
                            equipment_cost_per_account.get(acct, 0.0) + portion
                        )

            coste_maquinas = sum(machine_cost_per_account.values())
            coste_moldes = sum(equipment_cost_per_account.values())
            coste_otros = balance - coste_maquinas - coste_moldes

            _logger.warning(
                "[%s] coste_maquinas=%.2f | coste_moldes=%.2f | coste_otros=%.2f",
                method, coste_maquinas, coste_moldes, coste_otros,
            )

            # ── 4. Todos los workorders del periodo ───────────────────────────
            all_workorders = self.env['mrp.workorder'].search([
                ('date_start', '>=', date_from),
                ('date_start', '<=', date_to),
                ('state', '=', 'done'),
            ])
            _logger.warning("[%s] Workorders en el periodo: %d", method, len(all_workorders))

            # Horas totales de máquina (todos los workcenters)
            horas_maquina_total = sum(wo.duration for wo in all_workorders) / 60.0
            _logger.warning("[%s] horas_maquina_total=%.2f", method, horas_maquina_total)

            # Horas por producto base (todos los workorders)
            hours_per_base_all = {}
            for wo in all_workorders:
                base_tmpl = self._r17_get_base_tmpl(wo.product_id)
                if not base_tmpl:
                    continue
                hours_per_base_all[base_tmpl] = (
                    hours_per_base_all.get(base_tmpl, 0.0) + wo.duration / 60.0
                )

            ctx['horas_maquina_total'] = horas_maquina_total
            ctx['hours_per_base_all'] = hours_per_base_all

            # ── 5. Distribuir coste_maquinas ──────────────────────────────────
            if machine_cost_per_account:
                self._r17_distribute_machine_costs(
                    machine_cost_per_account, all_workorders, ctx
                )

            # ── 6. Distribuir coste_moldes ────────────────────────────────────
            if equipment_cost_per_account:
                self._r17_distribute_mold_costs(
                    equipment_cost_per_account, all_workorders, ctx
                )

            # ── 7. Distribuir coste_otros ─────────────────────────────────────
            if coste_otros and horas_maquina_total > 0:
                self._r17_distribute_otros(coste_otros, ctx)
            elif coste_otros:
                _logger.warning(
                    "[%s] coste_otros=%.2f pero horas_maquina_total=0; no se distribuye.",
                    method, coste_otros,
                )

    # =========================================================================
    # R17 LEGACY
    # =========================================================================

    def compute_r17_legacy(self, li):
        """Versión legacy de compute_r17: usa mrp.production.legacy para las
        horas de distribución en lugar de mrp.workorder.

        · coste_maquinas: distribuido con tiempos de mrp.production.legacy por
          machine_id → product base.
        · coste_moldes: sin información de moldes en legacy → se suma a
          coste_otros y se distribuye igual que éste.
        · coste_otros + coste_moldes: distribuidos con horas legacy por producto base.
        """
        for rec in self:
            method = 'R17_LEGACY'
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

            company = self.env.company
            machine_plan = company.analytic_machine_plan_id
            equipment_plan = company.analytic_equipment_plan_id

            if not machine_plan:
                _logger.warning("[%s] No está configurado analytic_machine_plan_id.", method)
                return
            if not equipment_plan:
                _logger.warning("[%s] No está configurado analytic_equipment_plan_id.", method)
                return

            product_field_id = company.product_field_id.name
            fixed_variable_field_id = company.fixed_variable_field_id.name
            variable_account = company.analytic_variable_account_id

            ctx = {
                'rec': rec,
                'li': li,
                'method': method,
                'date_from_d': date_from_d,
                'date_to_d': date_to_d,
                'product_field_id': product_field_id,
                'fixed_variable_field_id': fixed_variable_field_id,
                'variable_account': variable_account,
                'balance': balance,
            }

            # ── 1. Obtener move.lines y calcular costes por plan ──────────────
            all_move_lines = li._get_expense_lines() | li._get_income_lines()

            machine_accounts = self.env['account.analytic.account'].search([
                ('plan_id', '=', machine_plan.id),
            ])
            equipment_accounts = self.env['account.analytic.account'].search([
                ('plan_id', '=', equipment_plan.id),
            ])
            machine_ids_str = {str(a.id): a for a in machine_accounts}
            equipment_ids_str = {str(a.id): a for a in equipment_accounts}

            machine_cost_per_account = {}
            equipment_cost_per_account = {}

            for line in all_move_lines:
                analytic_dist = line.analytic_distribution or {}
                line_balance = line.balance
                for str_id, pct in analytic_dist.items():
                    portion = line_balance * pct / 100.0
                    if str_id in machine_ids_str:
                        acct = machine_ids_str[str_id]
                        machine_cost_per_account[acct] = (
                            machine_cost_per_account.get(acct, 0.0) + portion
                        )
                    elif str_id in equipment_ids_str:
                        acct = equipment_ids_str[str_id]
                        equipment_cost_per_account[acct] = (
                            equipment_cost_per_account.get(acct, 0.0) + portion
                        )

            coste_maquinas = sum(machine_cost_per_account.values())
            coste_moldes = sum(equipment_cost_per_account.values())
            coste_otros = balance - coste_maquinas - coste_moldes
            coste_otros_total = coste_otros + coste_moldes  # moldes → otros en legacy

            _logger.warning(
                "[%s] coste_maquinas=%.2f | coste_moldes=%.2f (→otros) | coste_otros=%.2f | otros_total=%.2f",
                method, coste_maquinas, coste_moldes, coste_otros, coste_otros_total,
            )

            # ── 2. Todos los registros legacy del periodo ─────────────────────
            all_legacy = self.env['mrp.production.legacy'].search([
                ('date', '>=', date_from_d),
                ('date', '<=', date_to_d),
            ])
            _logger.warning("[%s] Registros legacy en el periodo: %d", method, len(all_legacy))

            # Horas totales legacy
            horas_legacy_total = sum(lr.time for lr in all_legacy)
            _logger.warning("[%s] horas_legacy_total=%.2f", method, horas_legacy_total)

            # Horas por producto base (todos los legacy)
            hours_per_base_legacy = {}
            for lr in all_legacy:
                base_tmpl = lr.parent_id or lr.name
                if not base_tmpl:
                    continue
                hours_per_base_legacy[base_tmpl] = (
                    hours_per_base_legacy.get(base_tmpl, 0.0) + lr.time
                )

            ctx['horas_legacy_total'] = horas_legacy_total
            ctx['hours_per_base_legacy'] = hours_per_base_legacy

            # ── 3. Distribuir coste_maquinas por máquina (legacy) ────────────
            for machine_acct, cost in machine_cost_per_account.items():
                if not cost:
                    continue
                self._r17_legacy_distribute_machine_cost(machine_acct, cost, ctx)

            # ── 4. Distribuir coste_otros + coste_moldes con horas legacy ─────
            if coste_otros_total and horas_legacy_total > 0:
                self._r17_legacy_distribute_otros(coste_otros_total, ctx)
            elif coste_otros_total:
                _logger.warning(
                    "[%s] coste_otros_total=%.2f pero horas_legacy_total=0; no se distribuye.",
                    method, coste_otros_total,
                )

    # =========================================================================
    # Helpers: creación de apuntes
    # =========================================================================

    def _r17_create_analytic_line(self, ctx, base_tmpl, cost, note):
        """Crea un apunte analítico de coste para un producto base."""
        rec = ctx['rec']
        li = ctx['li']
        analytic_account = self.check_or_create_analytic_account(base_tmpl)
        product_pp = base_tmpl.product_variant_ids[:1]
        self.env['account.analytic.line'].create({
            'product_id': product_pp.id if product_pp else False,
            'name': f"{li.template_id.name} - {rec.name} | {base_tmpl.name}",
            'amount': -abs(cost),
            'date': ctx['rec'].date_to,
            ctx['product_field_id']: analytic_account.id,
            ctx['fixed_variable_field_id']: ctx['variable_account'].id if ctx['variable_account'] else False,
            'analytic_distribution_id': rec.id,
            'analytic_distribution_template_id': li.template_id.id,
            'analytic_distribution_note': note,
        })

    def _r17_get_base_tmpl(self, product):
        """Devuelve el product.template base a partir de un product.product."""
        if product.pnt_product_type == 'packing' and product.pnt_parent_id:
            return product.pnt_parent_id
        return product.product_tmpl_id

    # =========================================================================
    # Helpers: distribución de máquinas (R17)
    # =========================================================================

    def _r17_distribute_machine_costs(self, machine_cost_per_account, all_workorders, ctx):
        """Distribuye el total de coste_maquinas entre productos base.

        Cuentas con workorders activos → tasa global sobre horas totales.
        Cuentas sin workorders → fallback por tag/BoM.
        """
        method = ctx['method']
        date_from = ctx['date_from']
        date_to = ctx['date_to']
        horas_maquina_total = ctx['horas_maquina_total']
        hours_per_base_all = ctx['hours_per_base_all']

        # Workcenters activos en el periodo
        active_wc_ids = set(all_workorders.mapped('workcenter_id').ids)

        active_cost = 0.0
        inactive = []  # [(machine_account, cost)]

        for acct, cost in machine_cost_per_account.items():
            if not cost:
                continue
            if acct.workcenter_id and acct.workcenter_id.id in active_wc_ids:
                active_cost += cost
                _logger.warning("[%s] Máquina activa '%s': coste=%.2f", method, acct.name, cost)
            else:
                inactive.append((acct, cost))
                _logger.warning("[%s] Máquina inactiva '%s': coste=%.2f → fallback", method, acct.name, cost)

        # Distribución global de cuentas activas
        if active_cost and horas_maquina_total > 0:
            global_rate = active_cost / horas_maquina_total
            _logger.warning(
                "[%s] coste_maquinas_activas=%.2f | horas_total=%.2f | tasa=%.4f €/h",
                method, active_cost, horas_maquina_total, global_rate,
            )
            for base_tmpl, hours in hours_per_base_all.items():
                cost_assigned = global_rate * hours
                note = (
                    f"Informe: {method} — Coste máquinas (tasa global)\n"
                    f"Producto base: {base_tmpl.name}\n"
                    f"─── Cálculo ───\n"
                    f"  Coste máquinas activas: {active_cost:.2f}\n"
                    f"  Horas máquina total: {horas_maquina_total:.2f} h\n"
                    f"  Tasa global: {global_rate:.4f} €/h\n"
                    f"  Horas producto: {hours:.2f} h\n"
                    f"  Coste asignado = {global_rate:.4f} × {hours:.2f} = {cost_assigned:.2f}"
                )
                self._r17_create_analytic_line(ctx, base_tmpl, cost_assigned, note)
                _logger.warning("[%s]   Máquinas: %s → %.2f h → %.2f€",
                                method, base_tmpl.name, hours, cost_assigned)
        elif active_cost:
            _logger.warning(
                "[%s] coste_maquinas_activas=%.2f pero horas_maquina_total=0; no se distribuye.",
                method, active_cost,
            )

        # Fallback para cuentas inactivas
        for acct, cost in inactive:
            self._r17_machine_fallback(acct, cost, ctx)

    def _r17_machine_fallback(self, machine_account, cost, ctx):
        """Fallback: máquina sin workorders en el periodo.
        Busca grupo por tag → productos base en BoM de esas máquinas → reparto equitativo."""
        method = ctx['method']
        workcenter = machine_account.workcenter_id
        if not workcenter:
            _logger.warning(
                "[%s] FALLBACK: cuenta '%s' sin workcenter_id, ignorada.",
                method, machine_account.name,
            )
            return

        company_tags = self.env.company.mrp_workcenter_tag_ids
        matching_tag = None
        for tag in workcenter.tag_ids:
            if tag in company_tags:
                matching_tag = tag
                break

        if not matching_tag:
            _logger.warning(
                "[%s] FALLBACK: workcenter '%s' sin etiqueta de grupo, ignorado.",
                method, workcenter.name,
            )
            return

        group_workcenters = self.env['mrp.workcenter'].search([
            ('tag_ids', 'in', matching_tag.ids),
        ])
        bom_operations = self.env['mrp.routing.workcenter'].search([
            ('workcenter_id', 'in', group_workcenters.ids),
        ])
        base_set = set()
        for op in bom_operations:
            tmpl = op.bom_id.product_tmpl_id
            if tmpl.pnt_product_type == 'packing' and tmpl.pnt_parent_id:
                base_set.add(tmpl.pnt_parent_id)
            elif tmpl:
                base_set.add(tmpl)

        if not base_set:
            _logger.warning(
                "[%s] FALLBACK: sin productos en BoM para grupo '%s', ignorado.",
                method, matching_tag.name,
            )
            return

        cost_each = cost / len(base_set)
        _logger.warning(
            "[%s] FALLBACK máquina '%s' (grupo '%s'): %d productos | %.2f€/producto",
            method, machine_account.name, matching_tag.name, len(base_set), cost_each,
        )
        for base_tmpl in base_set:
            note = (
                f"Informe: {method} — Coste máquina (FALLBACK sin producción)\n"
                f"Máquina: {machine_account.name} | Workcenter: {workcenter.name}\n"
                f"Grupo (tag): {matching_tag.name}\n"
                f"Producto base: {base_tmpl.name}\n"
                f"─── Reparto ───\n"
                f"  Coste máquina: {cost:.2f}\n"
                f"  Sin workorders → reparto equitativo entre {len(base_set)} productos.\n"
                f"  Coste asignado: {cost_each:.2f}"
            )
            self._r17_create_analytic_line(ctx, base_tmpl, cost_each, note)

    # =========================================================================
    # Helpers: distribución de moldes (R17)
    # =========================================================================

    def _r17_distribute_mold_costs(self, equipment_cost_per_account, all_workorders, ctx):
        """Distribuye el total de coste_moldes entre productos base.

        Cuentas con workorders activos → tasa global sobre horas con molde.
        Cuentas sin workorders → fallback por product.template.
        """
        method = ctx['method']

        # Workorders con molde asignado en su producción → mapa equipment → workorders
        wos_by_equipment = {}
        for wo in all_workorders:
            tool = wo.production_id.mrp_tool_id
            if not tool:
                continue
            equip = tool.pnt_tool_id
            if not equip:
                continue
            if equip not in wos_by_equipment:
                wos_by_equipment[equip] = self.env['mrp.workorder']
            wos_by_equipment[equip] |= wo

        # Horas totales de workorders con molde
        horas_molde_total = sum(
            wo.duration for wos in wos_by_equipment.values() for wo in wos
        ) / 60.0
        _logger.warning("[%s] horas_molde_total=%.2f", method, horas_molde_total)

        # Horas por producto base (sólo workorders con molde)
        hours_per_base_mold = {}
        for wos in wos_by_equipment.values():
            for wo in wos:
                base_tmpl = self._r17_get_base_tmpl(wo.product_id)
                if not base_tmpl:
                    continue
                hours_per_base_mold[base_tmpl] = (
                    hours_per_base_mold.get(base_tmpl, 0.0) + wo.duration / 60.0
                )

        active_cost = 0.0
        inactive = []  # [(equipment_account, cost)]

        for acct, cost in equipment_cost_per_account.items():
            if not cost:
                continue
            equip = acct.equipment_id
            if equip and equip in wos_by_equipment:
                active_cost += cost
                _logger.warning("[%s] Molde activo '%s': coste=%.2f", method, acct.name, cost)
            else:
                inactive.append((acct, cost))
                _logger.warning("[%s] Molde inactivo '%s': coste=%.2f → fallback", method, acct.name, cost)

        # Distribución global de cuentas de molde activas
        if active_cost and horas_molde_total > 0:
            global_mold_rate = active_cost / horas_molde_total
            _logger.warning(
                "[%s] coste_moldes_activos=%.2f | horas_molde=%.2f | tasa=%.4f €/h",
                method, active_cost, horas_molde_total, global_mold_rate,
            )
            for base_tmpl, hours in hours_per_base_mold.items():
                cost_assigned = global_mold_rate * hours
                note = (
                    f"Informe: {method} — Coste moldes (tasa global)\n"
                    f"Producto base: {base_tmpl.name}\n"
                    f"─── Cálculo ───\n"
                    f"  Coste moldes activos: {active_cost:.2f}\n"
                    f"  Horas molde total: {horas_molde_total:.2f} h\n"
                    f"  Tasa global: {global_mold_rate:.4f} €/h\n"
                    f"  Horas producto (con molde): {hours:.2f} h\n"
                    f"  Coste asignado = {global_mold_rate:.4f} × {hours:.2f} = {cost_assigned:.2f}"
                )
                self._r17_create_analytic_line(ctx, base_tmpl, cost_assigned, note)
                _logger.warning("[%s]   Moldes: %s → %.2f h → %.2f€",
                                method, base_tmpl.name, hours, cost_assigned)
        elif active_cost:
            _logger.warning(
                "[%s] coste_moldes_activos=%.2f pero horas_molde_total=0; no se distribuye.",
                method, active_cost,
            )

        # Fallback para cuentas de molde inactivas
        for acct, cost in inactive:
            self._r17_mold_fallback(acct, cost, ctx)

    def _r17_mold_fallback(self, equipment_account, cost, ctx):
        """Fallback: molde sin workorders en el periodo.
        Busca mrp.product.tool con ese equipment y product_tmpl_id.pnt_product_type='final'
        → reparto equitativo entre esos productos base."""
        method = ctx['method']
        equipment = equipment_account.equipment_id
        if not equipment:
            _logger.warning(
                "[%s] FALLBACK molde: cuenta '%s' sin equipment_id, ignorada.",
                method, equipment_account.name,
            )
            return

        tools = self.env['mrp.product.tool'].search([
            ('pnt_tool_id', '=', equipment.id),
            ('product_tmpl_id.pnt_product_type', '=', 'final'),
        ])
        final_products = tools.mapped('product_tmpl_id')

        if not final_products:
            _logger.warning(
                "[%s] FALLBACK molde '%s': sin productos finales, ignorado.",
                method, equipment_account.name,
            )
            return

        cost_each = cost / len(final_products)
        _logger.warning(
            "[%s] FALLBACK molde '%s': %d productos | %.2f€/producto",
            method, equipment_account.name, len(final_products), cost_each,
        )
        for base_tmpl in final_products:
            note = (
                f"Informe: {method} — Coste molde (FALLBACK sin producción)\n"
                f"Molde: {equipment_account.name} | Equipo: {equipment.name}\n"
                f"Producto base: {base_tmpl.name}\n"
                f"─── Reparto ───\n"
                f"  Coste molde: {cost:.2f}\n"
                f"  Sin workorders → reparto equitativo entre {len(final_products)} productos.\n"
                f"  Coste asignado: {cost_each:.2f}"
            )
            self._r17_create_analytic_line(ctx, base_tmpl, cost_each, note)

    # =========================================================================
    # Helpers: distribución de otros (R17)
    # =========================================================================

    def _r17_distribute_otros(self, coste_otros, ctx):
        """Distribuye coste_otros proporcionalmente a horas de máquina por producto base
        usando todos los mrp.workorder del periodo."""
        method = ctx['method']
        horas_maquina_total = ctx['horas_maquina_total']
        hours_per_base_all = ctx['hours_per_base_all']

        global_otros_rate = coste_otros / horas_maquina_total
        _logger.warning(
            "[%s] coste_otros=%.2f | horas=%.2f | tasa=%.4f €/h",
            method, coste_otros, horas_maquina_total, global_otros_rate,
        )
        for base_tmpl, hours in hours_per_base_all.items():
            cost_assigned = global_otros_rate * hours
            note = (
                f"Informe: {method} — Coste otros\n"
                f"Producto base: {base_tmpl.name}\n"
                f"─── Cálculo ───\n"
                f"  Coste otros: {coste_otros:.2f}\n"
                f"  Horas máquina total: {horas_maquina_total:.2f} h\n"
                f"  Tasa global: {global_otros_rate:.4f} €/h\n"
                f"  Horas producto: {hours:.2f} h\n"
                f"  Coste asignado = {global_otros_rate:.4f} × {hours:.2f} = {cost_assigned:.2f}"
            )
            self._r17_create_analytic_line(ctx, base_tmpl, cost_assigned, note)
            _logger.warning("[%s]   Otros: %s → %.2f h → %.2f€",
                            method, base_tmpl.name, hours, cost_assigned)

    # =========================================================================
    # Helpers: distribución legacy
    # =========================================================================

    def _r17_legacy_distribute_machine_cost(self, machine_account, cost, ctx):
        """Distribuye el coste de una máquina usando registros legacy.
        Si hay legacy → proporcional a horas × qty por producto base.
        Si no hay legacy → fallback por tag/BoM (comparte lógica con R17)."""
        method = ctx['method']
        date_from_d = ctx['date_from_d']
        date_to_d = ctx['date_to_d']

        legacy_recs = self.env['mrp.production.legacy'].search([
            ('machine_id', '=', machine_account.id),
            ('date', '>=', date_from_d),
            ('date', '<=', date_to_d),
        ])
        _logger.warning(
            "[%s] Máquina '%s': coste=%.2f, registros legacy=%d",
            method, machine_account.name, cost, len(legacy_recs),
        )

        if legacy_recs:
            hours_per_base = {}
            for lr in legacy_recs:
                base_tmpl = lr.parent_id or lr.name
                if not base_tmpl:
                    continue
                hours_per_base[base_tmpl] = hours_per_base.get(base_tmpl, 0.0) + lr.time

            total_hours = sum(hours_per_base.values())
            if total_hours <= 0:
                _logger.warning(
                    "[%s]   Máquina '%s': total horas legacy=0, ignorado.",
                    method, machine_account.name,
                )
                return

            for base_tmpl, hours in hours_per_base.items():
                proportion = hours / total_hours
                cost_assigned = cost * proportion
                note = (
                    f"Informe: {method} — Coste máquina (Legacy)\n"
                    f"Máquina: {machine_account.name}\n"
                    f"Producto base: {base_tmpl.name}\n"
                    f"─── Cálculo ───\n"
                    f"  Coste máquina: {cost:.2f}\n"
                    f"  Horas legacy producto: {hours:.2f} h\n"
                    f"  Horas legacy total: {total_hours:.2f} h\n"
                    f"  Proporción: {proportion * 100:.4f}%\n"
                    f"  Coste asignado: {cost_assigned:.2f}"
                )
                self._r17_create_analytic_line(ctx, base_tmpl, cost_assigned, note)
                _logger.warning("[%s]   Legacy: %s → %.2f h (%.4f%%) → %.2f€",
                                method, base_tmpl.name, hours, proportion * 100, cost_assigned)
        else:
            _logger.warning(
                "[%s]   Máquina '%s' sin legacy → FALLBACK por tag/BoM.",
                method, machine_account.name,
            )
            # Reutilizamos el fallback de R17 adaptando el ctx (sin date_from/date_to → no se usa aquí)
            self._r17_machine_fallback(machine_account, cost, ctx)

    def _r17_legacy_distribute_otros(self, coste_otros_total, ctx):
        """Distribuye coste_otros + coste_moldes usando horas legacy por producto base."""
        method = ctx['method']
        horas_legacy_total = ctx['horas_legacy_total']
        hours_per_base_legacy = ctx['hours_per_base_legacy']

        rate = coste_otros_total / horas_legacy_total
        _logger.warning(
            "[%s] coste_otros_total=%.2f | horas_legacy=%.2f | tasa=%.4f €/h",
            method, coste_otros_total, horas_legacy_total, rate,
        )
        for base_tmpl, hours in hours_per_base_legacy.items():
            cost_assigned = rate * hours
            note = (
                f"Informe: {method} — Coste otros + moldes (Legacy)\n"
                f"Producto base: {base_tmpl.name}\n"
                f"─── Cálculo ───\n"
                f"  Coste otros + moldes: {coste_otros_total:.2f}\n"
                f"  Horas legacy total: {horas_legacy_total:.2f} h\n"
                f"  Tasa: {rate:.4f} €/h\n"
                f"  Horas legacy producto: {hours:.2f} h\n"
                f"  Coste asignado = {rate:.4f} × {hours:.2f} = {cost_assigned:.2f}"
            )
            self._r17_create_analytic_line(ctx, base_tmpl, cost_assigned, note)
            _logger.warning("[%s]   Otros legacy: %s → %.2f h → %.2f€",
                            method, base_tmpl.name, hours, cost_assigned)
