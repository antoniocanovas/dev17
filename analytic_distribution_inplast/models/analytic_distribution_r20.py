# -*- coding: utf-8 -*-
# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
#
# R20: Distribución de salarios de planificación entre productos base vendidos.
#
# Objetivo:
#   Repartir una fracción del balance (determinada por el parámetro porcentual
#   `sale_estimation`) entre los productos base (pnt_parent_id de los packings),
#   proporcionalmente al número de líneas de pedido de venta confirmadas en el
#   periodo para productos de tipo 'packing'.
#
# Fuente del coste:
#   li.balance × sale_estimation / 100
#   → solo se reparte ese porcentaje del balance, no el total.
#
# Base de reparto:
#   Líneas de pedido de venta confirmados (state in ['sale', 'done']) del periodo,
#   con productos de tipo 'packing'. Se excluyen borradores y cancelados.
#   El reparto es por número de líneas: una línea = una unidad de trabajo.
#   El coste se imputa al producto base (pnt_parent_id del packing).
from odoo import models
import logging

_logger = logging.getLogger(__name__)


class AnalyticDistribution(models.Model):
    _inherit = 'analytic.distribution'

    def compute_r20(self, li):
        """Distribuye sale_estimation % del balance entre los productos base,
        proporcionalmente al número de líneas de pedido de venta confirmadas
        en el periodo para productos de tipo packing.

        Parámetros:
            li  (analytic.distribution.line): línea con el template R20 que
                contiene el balance contable a distribuir.
        """
        for rec in self:
            method = 'R20'
            balance = li.balance
            _logger.warning("[%s] Iniciando cálculo. balance=%.2f", method, balance)
            if not balance:
                _logger.warning("[%s] SALIDA: balance es 0 o nulo.", method)
                return

            sale_pct = rec.sale_estimation
            _logger.warning("[%s] sale_estimation=%.4f%%", method, sale_pct)
            if not sale_pct:
                _logger.warning("[%s] SALIDA: sale_estimation es 0.", method)
                return

            amount_to_distribute = balance * sale_pct / 100.0
            _logger.warning("[%s] Importe a repartir = %.2f × %.4f%% = %.2f",
                            method, balance, sale_pct, amount_to_distribute)

            date_from = rec.date_from
            date_to = rec.date_to
            _logger.warning("[%s] Periodo: %s → %s", method, date_from, date_to)

            # ------------------------------------------------------------------
            # 1. Líneas de pedido de venta confirmados del período para
            #    productos de tipo packing.
            #    Se excluyen borradores (draft) y cancelados (cancel).
            # ------------------------------------------------------------------
            sale_lines = self.env['sale.order.line'].search([
                ('order_id.state', 'in', ['sale', 'done']),
                ('order_id.date_order', '>=', date_from),
                ('order_id.date_order', '<=', date_to),
                ('product_id.pnt_product_type', '=', 'packing'),
            ])
            _logger.warning("[%s] Líneas de venta packing encontradas: %d", method, len(sale_lines))
            if not sale_lines:
                _logger.warning("[%s] SALIDA: no hay líneas de venta en el periodo.", method)
                return

            # ------------------------------------------------------------------
            # 2. Acumulación de nº de líneas por producto base.
            #    lines_per_base: { product.template (base): count }
            # ------------------------------------------------------------------
            lines_per_base = {}
            for sl in sale_lines:
                base_tmpl = sl.product_id.pnt_parent_id
                if not base_tmpl:
                    _logger.warning(
                        "[%s]   Packing '%s' sin pnt_parent_id, ignorado.", method, sl.product_id.name
                    )
                    continue
                lines_per_base[base_tmpl] = lines_per_base.get(base_tmpl, 0) + 1

            total_lines = sum(lines_per_base.values())
            _logger.warning("[%s] Total líneas válidas: %d | Productos base distintos: %d",
                            method, total_lines, len(lines_per_base))
            if not total_lines:
                _logger.warning("[%s] SALIDA: sin líneas válidas tras filtrar pnt_parent_id.", method)
                return

            # ------------------------------------------------------------------
            # 3. Campos de la línea analítica.
            # ------------------------------------------------------------------
            product_field_id = self.env.company.product_field_id.name
            fixed_variable_field_id = self.env.company.fixed_variable_field_id.name
            department_field_id = self.env.company.department_field_id.name
            sale_dept = self.env.company.analytic_sale_department_id
            variable_account = self.env.company.analytic_variable_account_id

            # ------------------------------------------------------------------
            # 4. Creación de apuntes analíticos: uno por producto base.
            # ------------------------------------------------------------------
            for base_tmpl, line_count in lines_per_base.items():
                proportion = line_count / total_lines
                cost = amount_to_distribute * proportion
                proportion_pct = proportion * 100

                base_product = base_tmpl.product_variant_ids[:1]
                analytic_account = self.check_or_create_analytic_account(base_tmpl)

                note = (
                    f"Informe: {method} — Salarios planificación ventas\n"
                    f"Producto base: {base_tmpl.name}\n"
                    f"─── Parámetros ───\n"
                    f"  Balance: {balance:.2f}\n"
                    f"  % Planificación ventas (sale_estimation): {sale_pct:.4f}%\n"
                    f"  Importe a repartir = {balance:.2f} × {sale_pct:.4f}% = {amount_to_distribute:.2f}\n"
                    f"─── Reparto ───\n"
                    f"  Líneas de venta del producto base: {line_count}\n"
                    f"  Total líneas de venta: {total_lines}\n"
                    f"  Proporción: {proportion_pct:.4f}%\n"
                    f"  Coste asignado = {amount_to_distribute:.2f} × {proportion_pct:.4f}% = {cost:.2f}"
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
                _logger.warning("[%s]   Apunte creado: %s | %d líneas → %.2f€ (%.4f%%)",
                                method, base_tmpl.name, line_count, cost, proportion_pct)
