# -*- coding: utf-8 -*-
# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
#
# R18: Distribución del coste de gestión de compras entre materias primas.
#
# Objetivo:
#   Repartir una fracción del balance (determinada por el parámetro porcentual
#   `purchase_estimation`) entre los productos de tipo materia prima ('dye',
#   'raw', 'additive'), proporcionalmente al número de líneas de pedido de
#   compra confirmadas en el periodo para estimar el esfuerzo de redacción y
#   gestión de pedidos.
#
# Fuente del coste:
#   li.balance × rec.purchase_estimation / 100
#   → solo se reparte ese porcentaje del balance, no el total.
#
# Base de reparto:
#   Para cada producto de tipo 'dye', 'raw' o 'additive':
#       líneas_producto = nº de líneas en pedidos de compra confirmados
#                         (state in ['purchase', 'done']) del periodo.
#   proporción_producto = líneas_producto / total_líneas
#   coste_producto      = importe_a_repartir × proporción_producto
#
# Pedidos excluidos:
#   - Borradores (state = 'draft')
#   - Cancelados  (state = 'cancel')
#
# Salida:
#   Un apunte analítico (account.analytic.line) por cada producto con líneas
#   de compra en el periodo, con importe negativo proporcional al nº de líneas.
from odoo import models
import logging
_logger = logging.getLogger(__name__)

PURCHASE_PRODUCT_TYPES = ('dye', 'raw', 'additive')


class AnalyticDistribution(models.Model):
    _inherit = 'analytic.distribution'

    def compute_r18(self, li):
        """Distribuye una fracción del balance (purchase_estimation %) entre los
        productos de tipo dye/raw/additive, proporcionalmente al número de líneas
        de pedido de compra confirmadas en el periodo.

        Parámetros:
            li  (analytic.distribution.line): línea con el template R18 que
                contiene el balance contable a distribuir.
        """
        for rec in self:
            method = 'R18'
            balance = li.balance
            _logger.warning("[%s] Iniciando cálculo. balance=%.2f", method, balance)
            if not balance:
                _logger.warning("[%s] SALIDA: balance es 0 o nulo.", method)
                return

            purchase_pct = rec.purchase_estimation
            _logger.warning("[%s] purchase_estimation=%.4f%%", method, purchase_pct)
            if not purchase_pct:
                _logger.warning("[%s] SALIDA: purchase_estimation es 0.", method)
                return

            amount_to_distribute = balance * purchase_pct / 100.0
            _logger.warning("[%s] Importe a repartir = %.2f × %.4f%% = %.2f",
                            method, balance, purchase_pct, amount_to_distribute)

            date_from = rec.date_from
            date_to = rec.date_to
            _logger.warning("[%s] Periodo: %s → %s", method, date_from, date_to)

            # ------------------------------------------------------------------
            # 1. Líneas de pedido de compra confirmadas del período para
            #    productos de tipo dye / raw / additive.
            #    Se excluyen borradores (draft) y cancelados (cancel).
            # ------------------------------------------------------------------
            purchase_lines = self.env['purchase.order.line'].search([
                ('order_id.state', 'in', ['purchase', 'done']),
                ('order_id.date_order', '>=', date_from),
                ('order_id.date_order', '<=', date_to),
                ('product_id.pnt_product_type', 'in', list(PURCHASE_PRODUCT_TYPES)),
            ])
            _logger.warning("[%s] Líneas de compra encontradas: %d", method, len(purchase_lines))
            if not purchase_lines:
                _logger.warning("[%s] SALIDA: no hay líneas de compra en el periodo.", method)
                return

            # ------------------------------------------------------------------
            # 2. Acumulación de nº de líneas por producto (product.product).
            #    lines_per_product: { product.product: count }
            # ------------------------------------------------------------------
            lines_per_product = {}
            for pl in purchase_lines:
                product = pl.product_id
                lines_per_product[product] = lines_per_product.get(product, 0) + 1

            total_lines = sum(lines_per_product.values())
            _logger.warning("[%s] Total líneas: %d | Productos distintos: %d",
                            method, total_lines, len(lines_per_product))

            # ------------------------------------------------------------------
            # 3. Campos de la línea analítica (misma convención que otros informes).
            # ------------------------------------------------------------------
            product_field_id = self.env.company.product_field_id.name
            fixed_variable_field_id = self.env.company.fixed_variable_field_id.name
            department_field_id = self.env.company.department_field_id.name
            admin_dept = self.env.company.analytic_administration_department_id
            variable_account = self.env.company.analytic_variable_account_id

            # ------------------------------------------------------------------
            # 4. Creación de apuntes analíticos: uno por producto.
            # ------------------------------------------------------------------
            for product, line_count in lines_per_product.items():
                proportion = line_count / total_lines
                cost = amount_to_distribute * proportion
                proportion_pct = proportion * 100

                note = (
                    f"Informe: {method}\n"
                    f"Producto: {product.name} [{product.pnt_product_type}]\n"
                    f"─── Parámetros ───\n"
                    f"  Balance a distribuir: {balance:.2f}\n"
                    f"  % estimación compras (purchase_estimation): {purchase_pct:.4f}%\n"
                    f"  Importe a repartir = {balance:.2f} × {purchase_pct:.4f}% = {amount_to_distribute:.2f}\n"
                    f"─── Reparto ───\n"
                    f"  Líneas de compra del producto: {line_count}\n"
                    f"  Total líneas de compra: {total_lines}\n"
                    f"  Proporción: {proportion_pct:.4f}%\n"
                    f"  Coste asignado = {amount_to_distribute:.2f} × {proportion_pct:.4f}% = {cost:.2f}"
                )

                analytic_account = self.check_or_create_analytic_account(product.product_tmpl_id)
                self.env['account.analytic.line'].create({
                    'product_id': product.id,
                    'name': (
                        f"{li.template_id.name} - {rec.name} | {product.name}"
                    ),
                    'amount': -abs(cost),
                    product_field_id: analytic_account.id,
                    fixed_variable_field_id: variable_account.id,
                    'analytic_distribution_id': rec.id,
                    'analytic_distribution_template_id': li.template_id.id,
                    'analytic_distribution_note': note,
                })
                _logger.warning("[%s]   Apunte creado: %s | %d líneas → %.2f€ (%.4f%%)",
                                method, product.name, line_count, cost, proportion_pct)
