# -*- coding: utf-8 -*-
# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
#
# R16: Distribución del coste de mantenimiento/paradas entre productos base.
#
# Objetivo:
#   Repartir el balance entre los productos base (tapones) en función de las
#   horas de paro y de producción registradas para cada máquina en el periodo.
#
# ─── FUENTES DE DATOS ─────────────────────────────────────────────────────────
#   · Horas de paro: campo `time` en mrp.maintenance.issue filtrado por
#     department_id == company_id.analytic_workshop_department_id y cuya
#     machine_id (account.analytic.account) tenga workcenter_id cumplimentado.
#   · Horas de producción: duración (minutos → horas) de mrp.workorder en
#     estado 'done' para el workcenter_id de cada máquina considerada.
#
# ─── CÁLCULO DE PRECIOS ───────────────────────────────────────────────────────
#   precio_bruto_paro       = balance / total_horas_paro
#   precio_bruto_produccion = balance / total_horas_produccion
#   pct = mrp_maintenance_time
#   precio_neto_paro        = precio_bruto_paro       * (1 - pct / 100)
#   precio_neto_produccion  = precio_bruto_produccion * (pct / 100)
#
#   importe_maquina = h_paro_maquina * precio_neto_paro
#                   + h_prod_maquina * precio_neto_produccion
#
#   La suma de importes por máquina es igual al balance.
#
# ─── DISTRIBUCIÓN POR PRODUCTO ────────────────────────────────────────────────
#   Para cada máquina con workorders de productos "packing" en el periodo:
#     · Se acumulan tapones base (pnt_parent_id) ponderados por qty × pnt_parent_qty.
#     · El importe de la máquina se reparte proporcionalmente entre ellos.
#
#   Fallback (máquina sin workorders en el periodo):
#     · Se buscan operaciones de BoM (mrp.routing.workcenter) que usen el
#       workcenter de la máquina o sus alternativos (alternative_workcenter_ids).
#     · Si el producto de la BoM es packing, se sube al producto base.
#     · El importe se reparte equitativamente entre todos los productos encontrados.
#
# ─── VALIDACIONES ────────────────────────────────────────────────────────────
#   · Si alguna máquina (machine_id en mrp.maintenance.issue del periodo) no
#     tiene workcenter_id asignado en account.analytic.account → UserError.
from odoo import models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AnalyticDistribution(models.Model):
    _inherit = 'analytic.distribution'

    def compute_r16(self, li):
        """Distribuye el balance de mantenimiento entre productos base en función
        de las horas de paro (mrp.maintenance.issue - taller) y de producción
        (mrp.workorder) registradas por máquina en el periodo.

        Parámetros:
            li  (analytic.distribution.line): línea con el template R16 que
                contiene el balance contable a distribuir.
        """
        for rec in self:
            method = 'R16'
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

            pct = rec.mrp_maintenance_time
            _logger.warning("[%s] mrp_maintenance_time=%.4f%%", method, pct)

            # Campos analíticos comunes
            product_field_id = self.env.company.product_field_id.name
            fixed_variable_field_id = self.env.company.fixed_variable_field_id.name
            department_field_id = self.env.company.department_field_id.name
            workshop_dept = self.env.company.analytic_workshop_department_id
            variable_account = self.env.company.analytic_variable_account_id

            # ── 1. Registros de mantenimiento en el periodo para TALLER ──────
            if not workshop_dept:
                _logger.warning("[%s] No está configurado analytic_workshop_department_id.", method)
                return

            maintenance_issues = self.env['mrp.maintenance.issue'].search([
                ('date', '>=', date_from_d),
                ('date', '<=', date_to_d),
                ('department_id', '=', workshop_dept.id),
            ])
            _logger.warning("[%s] Registros mantenimiento taller: %d", method, len(maintenance_issues))
            if not maintenance_issues:
                _logger.warning("[%s] SALIDA: sin registros de mantenimiento en el periodo.", method)
                return

            # ── 2. Obtener máquinas únicas y validar workcenter_id ───────────
            machines = maintenance_issues.mapped('machine_id')
            _logger.warning("[%s] Máquinas con registros de paro: %d", method, len(machines))

            machines_without_wc = machines.filtered(lambda m: not m.workcenter_id)
            if machines_without_wc:
                names = ', '.join(machines_without_wc.mapped('name'))
                raise UserError(
                    f"[{method}] Las siguientes cuentas analíticas de máquina no tienen "
                    f"workcenter_id asignado. Por favor, asígnalas antes de calcular:\n{names}"
                )

            # ── 3. Horas de paro por máquina ─────────────────────────────────
            stop_hours_per_machine = {}
            for issue in maintenance_issues:
                machine = issue.machine_id
                stop_hours_per_machine[machine] = stop_hours_per_machine.get(machine, 0.0) + issue.time

            total_stop_hours = sum(stop_hours_per_machine.values())
            _logger.warning("[%s] Total horas de paro: %.2f", method, total_stop_hours)

            # ── 4. Horas de producción por máquina ───────────────────────────
            prod_hours_per_machine = {}
            for machine in machines:
                workcenter = machine.workcenter_id
                workorders = self.env['mrp.workorder'].search([
                    ('workcenter_id', '=', workcenter.id),
                    ('date_start', '>=', date_from),
                    ('date_start', '<=', date_to),
                    ('state', '=', 'done'),
                ])
                prod_hours = sum(wo.duration for wo in workorders) / 60.0
                prod_hours_per_machine[machine] = prod_hours
                _logger.warning("[%s]   Máquina '%s': %.2f h producción (%d workorders)",
                                method, machine.name, prod_hours, len(workorders))

            total_prod_hours = sum(prod_hours_per_machine.values())
            _logger.warning("[%s] Total horas de producción: %.2f", method, total_prod_hours)

            # ── 5. Precios brutos y netos ─────────────────────────────────────
            if total_stop_hours <= 0:
                _logger.warning("[%s] SALIDA: total horas de paro = 0.", method)
                return

            precio_bruto_paro = balance / total_stop_hours
            precio_neto_paro = precio_bruto_paro * (1 - pct / 100.0)
            _logger.warning("[%s] precio_bruto_paro=%.4f | precio_neto_paro=%.4f",
                            method, precio_bruto_paro, precio_neto_paro)

            if total_prod_hours > 0:
                precio_bruto_produccion = balance / total_prod_hours
                precio_neto_produccion = precio_bruto_produccion * (pct / 100.0)
            else:
                precio_bruto_produccion = 0.0
                precio_neto_produccion = 0.0
                _logger.warning("[%s] Total horas de producción = 0; precio producción = 0.", method)

            _logger.warning("[%s] precio_bruto_produccion=%.4f | precio_neto_produccion=%.4f",
                            method, precio_bruto_produccion, precio_neto_produccion)

            # ── 6. Importe por máquina y distribución a productos ─────────────
            ctx = {
                'rec': rec,
                'li': li,
                'method': method,
                'date_from': date_from,
                'date_to': date_to,
                'product_field_id': product_field_id,
                'fixed_variable_field_id': fixed_variable_field_id,
                'department_field_id': department_field_id,
                'workshop_dept': workshop_dept,
                'variable_account': variable_account,
                'balance': balance,
                'pct': pct,
                'precio_bruto_paro': precio_bruto_paro,
                'precio_neto_paro': precio_neto_paro,
                'precio_bruto_produccion': precio_bruto_produccion,
                'precio_neto_produccion': precio_neto_produccion,
                'total_stop_hours': total_stop_hours,
                'total_prod_hours': total_prod_hours,
            }

            for machine in machines:
                h_paro = stop_hours_per_machine.get(machine, 0.0)
                h_prod = prod_hours_per_machine.get(machine, 0.0)
                importe_maquina = h_paro * precio_neto_paro + h_prod * precio_neto_produccion
                _logger.warning(
                    "[%s] Máquina '%s': h_paro=%.2f h_prod=%.2f importe=%.2f",
                    method, machine.name, h_paro, h_prod, importe_maquina
                )
                if not importe_maquina:
                    continue
                self._r16_distribute_machine_cost(machine, importe_maquina, h_paro, h_prod, ctx)

    # =========================================================================
    # Helpers internos
    # =========================================================================

    def _r16_create_analytic_line(self, ctx, base_tmpl, cost, note):
        """Crea un apunte analítico de coste de mantenimiento para un producto base."""
        rec = ctx['rec']
        li = ctx['li']
        analytic_account = self.check_or_create_analytic_account(base_tmpl)
        product_pp = base_tmpl.product_variant_ids[:1]
        self.env['account.analytic.line'].create({
            'product_id': product_pp.id if product_pp else False,
            'name': f"{li.template_id.name} - {rec.name} | {base_tmpl.name}",
            'amount': -abs(cost),
            ctx['product_field_id']: analytic_account.id,
            ctx['fixed_variable_field_id']: ctx['variable_account'].id if ctx['variable_account'] else False,
            'analytic_distribution_id': rec.id,
            'analytic_distribution_template_id': li.template_id.id,
            'analytic_distribution_note': note,
        })

    def _r16_distribute_machine_cost(self, machine, importe_maquina, h_paro, h_prod, ctx):
        """Distribuye el importe de una máquina entre sus productos base.

        · Con workorders de packing en el periodo → proporcional a tapones fabricados.
        · Sin workorders → reparto equitativo entre productos fabricables en sus BoM.
        """
        method = ctx['method']
        workcenter = machine.workcenter_id

        # Buscar workorders de packing en el periodo para este workcenter
        workorders = self.env['mrp.workorder'].search([
            ('workcenter_id', '=', workcenter.id),
            ('date_start', '>=', ctx['date_from']),
            ('date_start', '<=', ctx['date_to']),
            ('state', '=', 'done'),
            ('product_id.pnt_product_type', '=', 'packing'),
        ])

        if workorders:
            self._r16_distribute_by_workorders(machine, importe_maquina, h_paro, h_prod, workorders, ctx)
        else:
            _logger.warning(
                "[%s]   Máquina '%s' sin workorders de packing → FALLBACK por BoM.",
                method, machine.name
            )
            self._r16_distribute_by_bom_fallback(machine, importe_maquina, h_paro, h_prod, ctx)

    def _r16_distribute_by_workorders(self, machine, importe_maquina, h_paro, h_prod, workorders, ctx):
        """Distribución con workorders: proporcional a tapones base fabricados."""
        method = ctx['method']
        workcenter = machine.workcenter_id

        # Acumular tapones base ponderados por qty × pnt_parent_qty
        qty_per_base = {}
        for wo in workorders:
            packing = wo.product_id
            base_tmpl = packing.pnt_parent_id
            if not base_tmpl:
                _logger.warning(
                    "[%s]   Workorder '%s' producto packing '%s' sin pnt_parent_id, ignorado.",
                    method, wo.name, packing.name
                )
                continue
            base_qty = wo.qty_production * (packing.pnt_parent_qty or 1.0)
            qty_per_base[base_tmpl] = qty_per_base.get(base_tmpl, 0.0) + base_qty

        total_qty = sum(qty_per_base.values())
        if total_qty <= 0:
            _logger.warning(
                "[%s]   Máquina '%s': total tapones base = 0, ignorado.",
                method, machine.name
            )
            return

        for base_tmpl, qty in qty_per_base.items():
            proportion = qty / total_qty
            cost = importe_maquina * proportion
            proportion_pct = proportion * 100
            note = (
                f"Informe: {method} — Distribución mantenimiento/producción\n"
                f"Máquina: {machine.name} | Workcenter: {workcenter.name}\n"
                f"Producto base: {base_tmpl.name}\n"
                f"─── Precios ───\n"
                f"  Balance: {ctx['balance']:.2f}\n"
                f"  % Mantenimiento: {ctx['pct']:.2f}%\n"
                f"  Precio bruto paro: {ctx['precio_bruto_paro']:.4f} €/h\n"
                f"  Precio neto paro: {ctx['precio_neto_paro']:.4f} €/h\n"
                f"  Precio bruto producción: {ctx['precio_bruto_produccion']:.4f} €/h\n"
                f"  Precio neto producción: {ctx['precio_neto_produccion']:.4f} €/h\n"
                f"─── Máquina ───\n"
                f"  Horas de paro: {h_paro:.2f} h | Horas de producción: {h_prod:.2f} h\n"
                f"  Importe máquina: {importe_maquina:.2f}\n"
                f"─── Reparto ───\n"
                f"  Tapones base fabricados (producto): {qty:.2f}\n"
                f"  Tapones base fabricados (total):    {total_qty:.2f}\n"
                f"  Proporción: {proportion_pct:.4f}%\n"
                f"  Coste asignado = {importe_maquina:.2f} × {proportion_pct:.4f}% = {cost:.2f}"
            )
            self._r16_create_analytic_line(ctx, base_tmpl, cost, note)
            _logger.warning("[%s]     %s → %.2f tapones (%.4f%%) → %.2f€",
                            method, base_tmpl.name, qty, proportion_pct, cost)

    def _r16_distribute_by_bom_fallback(self, machine, importe_maquina, h_paro, h_prod, ctx):
        """Fallback: sin workorders de packing. Busca productos fabricables en BoM
        donde aparezca el workcenter de la máquina (directa o como alternativa).
        Reparte equitativamente entre todos los productos base encontrados."""
        method = ctx['method']
        workcenter = machine.workcenter_id
        all_wcs = workcenter | workcenter.alternative_workcenter_ids

        bom_operations = self.env['mrp.routing.workcenter'].search([
            ('workcenter_id', 'in', all_wcs.ids),
        ])
        bom_tmpls = bom_operations.mapped('bom_id.product_tmpl_id')

        base_set = set()
        for tmpl in bom_tmpls:
            if tmpl.pnt_product_type == 'packing' and tmpl.pnt_parent_id:
                base_set.add(tmpl.pnt_parent_id)
            else:
                base_set.add(tmpl)

        if not base_set:
            _logger.warning(
                "[%s]   FALLBACK: sin productos en BoM para '%s', ignorado.",
                method, machine.name
            )
            return

        cost_each = importe_maquina / len(base_set)
        _logger.warning(
            "[%s]   FALLBACK '%s': %d productos | coste/producto=%.2f",
            method, machine.name, len(base_set), cost_each
        )

        for base_tmpl in base_set:
            note = (
                f"Informe: {method} — Distribución mantenimiento/producción (FALLBACK sin producción)\n"
                f"Máquina: {machine.name} | Workcenter: {workcenter.workcenter_id.name if hasattr(workcenter, 'workcenter_id') else workcenter.name}\n"
                f"Producto base: {base_tmpl.name}\n"
                f"─── Precios ───\n"
                f"  Balance: {ctx['balance']:.2f}\n"
                f"  % Mantenimiento: {ctx['pct']:.2f}%\n"
                f"  Precio bruto paro: {ctx['precio_bruto_paro']:.4f} €/h\n"
                f"  Precio neto paro: {ctx['precio_neto_paro']:.4f} €/h\n"
                f"  Precio bruto producción: {ctx['precio_bruto_produccion']:.4f} €/h\n"
                f"  Precio neto producción: {ctx['precio_neto_produccion']:.4f} €/h\n"
                f"─── Máquina ───\n"
                f"  Horas de paro: {h_paro:.2f} h | Horas de producción: {h_prod:.2f} h\n"
                f"  Importe máquina: {importe_maquina:.2f}\n"
                f"─── Reparto ───\n"
                f"  Sin workorders → reparto equitativo entre {len(base_set)} productos.\n"
                f"  Coste asignado = {importe_maquina:.2f} / {len(base_set)} = {cost_each:.2f}"
            )
            self._r16_create_analytic_line(ctx, base_tmpl, cost_each, note)
