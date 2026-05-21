# -*- coding: utf-8 -*-
# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
#
# R21: Distribución de salarios MRP entre productos base fabricados.
#
# Objetivo:
#   Repartir una fracción del balance (determinada por `sale_mrp_estimation`)
#   entre los productos base (pnt_parent_id de los packings) fabricados en el
#   periodo, en función del tiempo de fabricación y la cantidad producida.
#
# ─── FUENTE DEL COSTE ─────────────────────────────────────────────────────────
#   li.balance × sale_mrp_estimation / 100
#
# ─── PRECIO HORA ─────────────────────────────────────────────────────────────
#   total_horas = Σ workorder.duration (min → h) de todos los mrp.workorder
#                 finalizados (state='done') en el periodo.
#   precio_hora = importe_a_repartir / total_horas
#
# ─── REPARTO ─────────────────────────────────────────────────────────────────
#   Para cada mrp.production finalizada del periodo con producto packing:
#     horas_mo   = Σ workorder.duration (min → h) de las órdenes de esa MO
#     base_qty   = mo.qty_produced × packing.pnt_parent_qty
#     coste_mo   = horas_mo × precio_hora
#
#   El coste_mo se acumula por producto base (pnt_parent_id).
#   Se genera un apunte analítico por producto base con el coste total acumulado.
from odoo import models
import logging

_logger = logging.getLogger(__name__)


class AnalyticDistribution(models.Model):
    _inherit = 'analytic.distribution'

    def compute_r21(self, li):
        """Distribuye sale_mrp_estimation % del balance entre los productos base
        fabricados en el periodo, ponderando por horas de fabricación.

        Parámetros:
            li  (analytic.distribution.line): línea con el template R21 que
                contiene el balance contable a distribuir.
        """
        for rec in self:
            method = 'R21'
            balance = li.balance
            _logger.warning("[%s] Iniciando cálculo. balance=%.2f", method, balance)
            if not balance:
                _logger.warning("[%s] SALIDA: balance es 0 o nulo.", method)
                return

            mrp_pct = rec.sale_mrp_estimation
            _logger.warning("[%s] sale_mrp_estimation=%.4f%%", method, mrp_pct)
            if not mrp_pct:
                _logger.warning("[%s] SALIDA: sale_mrp_estimation es 0.", method)
                return

            amount_to_distribute = balance * mrp_pct / 100.0
            _logger.warning("[%s] Importe a repartir = %.2f × %.4f%% = %.2f",
                            method, balance, mrp_pct, amount_to_distribute)

            date_from = rec.date_from
            date_to = rec.date_to
            _logger.warning("[%s] Periodo: %s → %s", method, date_from, date_to)

            # ------------------------------------------------------------------
            # 1. Total de horas de todos los workorders finalizados del periodo.
            # ------------------------------------------------------------------
            all_workorders = self.env['mrp.workorder'].search([
                ('date_start', '>=', date_from),
                ('date_start', '<=', date_to),
                ('state', '=', 'done'),
            ])
            total_hours = sum(wo.duration for wo in all_workorders) / 60.0
            _logger.warning("[%s] Workorders en periodo: %d | Total horas: %.2f",
                            method, len(all_workorders), total_hours)

            if total_hours <= 0:
                _logger.warning("[%s] SALIDA: total horas de producción = 0.", method)
                return

            precio_hora = amount_to_distribute / total_hours
            _logger.warning("[%s] Precio hora = %.2f / %.2f h = %.4f €/h",
                            method, amount_to_distribute, total_hours, precio_hora)

            # ------------------------------------------------------------------
            # 2. Órdenes de producción finalizadas del periodo para packing.
            # ------------------------------------------------------------------
            productions = self.env['mrp.production'].search([
                ('date_finished', '>=', date_from),
                ('date_finished', '<=', date_to),
                ('state', '=', 'done'),
                ('product_id.pnt_product_type', '=', 'packing'),
            ])
            _logger.warning("[%s] Órdenes de producción packing: %d", method, len(productions))

            if not productions:
                _logger.warning("[%s] SALIDA: no hay órdenes de producción en el periodo.", method)
                return

            # ------------------------------------------------------------------
            # 3. Acumular coste por producto base.
            #    coste_mo = horas_workorders_mo × precio_hora
            # ------------------------------------------------------------------
            cost_per_base = {}
            qty_per_base = {}

            for mo in productions:
                packing = mo.product_id
                base_tmpl = packing.pnt_parent_id
                if not base_tmpl:
                    _logger.warning(
                        "[%s]   MO '%s' packing '%s' sin pnt_parent_id, ignorado.",
                        method, mo.name, packing.name
                    )
                    continue

                mo_hours = sum(wo.duration for wo in mo.workorder_ids) / 60.0
                mo_cost = mo_hours * precio_hora
                base_qty = mo.qty_produced * (packing.pnt_parent_qty or 1.0)

                cost_per_base[base_tmpl] = cost_per_base.get(base_tmpl, 0.0) + mo_cost
                qty_per_base[base_tmpl] = qty_per_base.get(base_tmpl, 0.0) + base_qty

                _logger.warning(
                    "[%s]   MO '%s' | base='%s' | %.2f h × %.4f €/h = %.2f€ | base_qty=%.2f",
                    method, mo.name, base_tmpl.name, mo_hours, precio_hora, mo_cost, base_qty
                )

            if not cost_per_base:
                _logger.warning("[%s] SALIDA: sin productos base con coste calculado.", method)
                return

            # ------------------------------------------------------------------
            # 4. Campos analíticos comunes.
            # ------------------------------------------------------------------
            product_field_id = self.env.company.product_field_id.name
            fixed_variable_field_id = self.env.company.fixed_variable_field_id.name
            department_field_id = self.env.company.department_field_id.name
            sale_dept = self.env.company.analytic_sale_department_id
            variable_account = self.env.company.analytic_variable_account_id

            # ------------------------------------------------------------------
            # 5. Crear apuntes analíticos por producto base.
            # ------------------------------------------------------------------
            total_cost_assigned = sum(cost_per_base.values())
            _logger.warning("[%s] Coste total asignado: %.2f (esperado: %.2f)",
                            method, total_cost_assigned, amount_to_distribute)

            for base_tmpl, cost in cost_per_base.items():
                qty = qty_per_base.get(base_tmpl, 0.0)
                cost_per_unit = (cost / qty) if qty else 0.0

                base_product = base_tmpl.product_variant_ids[:1]
                analytic_account = self.check_or_create_analytic_account(base_tmpl)

                note = (
                    f"Informe: {method} — Salarios MRP / fabricación\n"
                    f"Producto base: {base_tmpl.name}\n"
                    f"─── Parámetros ───\n"
                    f"  Balance: {balance:.2f}\n"
                    f"  % MRP ventas (sale_mrp_estimation): {mrp_pct:.4f}%\n"
                    f"  Importe a repartir = {balance:.2f} × {mrp_pct:.4f}% = {amount_to_distribute:.2f}\n"
                    f"  Total horas producción periodo: {total_hours:.2f} h\n"
                    f"  Precio hora = {amount_to_distribute:.2f} / {total_hours:.2f} = {precio_hora:.4f} €/h\n"
                    f"─── Reparto ───\n"
                    f"  Unidades base fabricadas: {qty:.2f}\n"
                    f"  Coste asignado: {cost:.2f}\n"
                    f"  Coste/unidad base: {cost_per_unit:.4f}"
                )

                self.env['account.analytic.line'].create({
                    'product_id': base_product.id if base_product else False,
                    'name': f"{li.template_id.name} - {rec.name} | {base_tmpl.name}",
                    'amount': -abs(cost),
                    'date': rec.date_to,
                    product_field_id: analytic_account.id,
                    fixed_variable_field_id: variable_account.id if variable_account else False,
                    'analytic_distribution_id': rec.id,
                    'analytic_distribution_template_id': li.template_id.id,
                    'analytic_distribution_note': note,
                })
                _logger.warning("[%s]   Apunte creado: %s → %.2f€ | %.2f u.base | %.4f €/u",
                                method, base_tmpl.name, cost, qty, cost_per_unit)
