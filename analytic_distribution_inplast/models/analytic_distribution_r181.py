# -*- coding: utf-8 -*-
# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
#
# R18.1: Distribución del coste de gestión de compras de asas.
#
# Idéntico a R18 salvo en el porcentaje y el tipo de producto:
#   R18   → purchase_estimation     | productos 'dye', 'raw', 'additive'
#   R18.1 → purchase_estimation_handle | productos categ_id.type = 'handle'
#
# Objetivo:
#   Repartir una fracción del balance (determinada por el parámetro porcentual
#   `purchase_estimation_handle`) entre los productos de tipo asa (categ_id.type
#   = 'handle'), proporcionalmente al número de líneas de pedido de compra
#   confirmadas en el periodo.
#
# Fuente del coste:
#   li.balance × rec.purchase_estimation_handle / 100
#
# Base de reparto:
#   Para cada producto con categ_id.type = 'handle':
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


class AnalyticDistribution(models.Model):
    _inherit = 'analytic.distribution'

    def compute_r181(self, li):
        """Distribuye una fracción del balance (purchase_estimation_handle %)
        entre los productos de tipo asa (categ_id.type = 'handle'),
        proporcionalmente al número de líneas de pedido de compra confirmadas
        en el periodo.

        Parámetros:
            li  (analytic.distribution.line): línea con el template R18.1 que
                contiene el balance contable a distribuir.
        """
        for rec in self:
            method = 'R18.1'
            balance = li.balance
            _logger.warning("[%s] Iniciando cálculo. balance=%.2f", method, balance)
            if not balance:
                _logger.warning("[%s] SALIDA: balance es 0 o nulo.", method)
                return

            purchase_pct = rec.purchase_estimation_handle
            _logger.warning("[%s] purchase_estimation_handle=%.4f%%", method, purchase_pct)
            if not purchase_pct:
                _logger.warning("[%s] SALIDA: purchase_estimation_handle es 0.", method)
                return

            amount_to_distribute = balance * purchase_pct / 100.0
            _logger.warning("[%s] Importe a repartir = %.2f × %.4f%% = %.2f",
                            method, balance, purchase_pct, amount_to_distribute)

            date_from = rec.date_from
            date_to = rec.date_to
            _logger.warning("[%s] Periodo: %s → %s", method, date_from, date_to)

            # ------------------------------------------------------------------
            # 1. Líneas de pedido de compra confirmadas del período para
            #    productos con categ_id.type = 'handle'.
            #    Se excluyen borradores (draft) y cancelados (cancel).
            # ------------------------------------------------------------------
            purchase_lines = self.env['purchase.order.line'].search([
                ('order_id.state', 'in', ['purchase', 'done']),
                ('order_id.date_order', '>=', date_from),
                ('order_id.date_order', '<=', date_to),
                ('product_id.categ_id.type', '=', 'handle'),
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
                    f"Producto: {product.name} [handle]\n"
                    f"─── Parámetros ───\n"
                    f"  Balance a distribuir: {balance:.2f}\n"
                    f"  % estimación compras asas (purchase_estimation_handle): {purchase_pct:.4f}%\n"
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
                    'name': f"{li.template_id.name} - {rec.name} | {product.name}",
                    'amount': -abs(cost),
                    'date': rec.date_to,
                    product_field_id: analytic_account.id,
                    fixed_variable_field_id: variable_account.id,
                    'analytic_distribution_id': rec.id,
                    'analytic_distribution_template_id': li.template_id.id,
                    'analytic_distribution_note': note,
                })
                _logger.warning("[%s]   Apunte creado: %s | %d líneas → %.2f€ (%.4f%%)",
                                method, product.name, line_count, cost, proportion_pct)
