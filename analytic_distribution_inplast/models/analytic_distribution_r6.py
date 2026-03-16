# -*- coding: utf-8 -*-
# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models


class AnalyticDistribution(models.Model):
    _inherit = 'analytic.distribution'

    def compute_r6(self, li):
        for rec in self:
            categ_types = ['raw_cistern', 'raw_sack', 'raw_pallet', 'raw_bag', 'raw_cardboard', 'raw_color']

            total_weight_before = 0.0
            total_weight_after  = 0.0

            # Total de kg en stock de MP en fecha de inicio:
            moves_before = self.env['stock.move.line'].search([
                ('product_id.categ_id.type', 'in', categ_types),
                ('date', '<=', rec.date_from),
                ('product_id.detailed_type','=','product'),
                '|',  # Operador "OR"
                ('location_id.usage', '=', 'internal'),
                ('location_dest_id.usage', '=', 'internal'),
            ], order='date')
            for move_line in moves_before:
                # Multiplicar la cantidad por el peso del producto.
                move_weight = move_line.qty_done * move_line.product_id.weight
                # Sumar o restar el peso según la dirección del movimiento.
                if move_line.location_id.usage == 'internal':
                    total_weight_before -= move_weight
                if move_line.location_dest_id.usage == 'internal':
                    total_weight_before += move_weight

            # Total de kg en stock de MP en fecha de fin:
            moves_after = self.env['stock.move.line'].search([
                ('product_id.categ_id.type', 'in', categ_types),
                ('date', '<=', rec.date_to),
                ('product_id.detailed_type', '=', 'product'),
                '|',  # Operador "OR"
                ('location_id.usage', '=', 'internal'),
                ('location_dest_id.usage', '=', 'internal'),
            ], order='date')
            for move_line in moves_after:
                # Multiplicar la cantidad por el peso del producto.
                move_weight = move_line.qty_done * move_line.product_id.weight
                # Sumar o restar el peso según la dirección del movimiento.
                if move_line.location_id.usage == 'internal':
                    total_weight_after -= move_weight
                if move_line.location_dest_id.usage == 'internal':
                    total_weight_after += move_weight
            # Peso medio entre inicio y fin de periodo:
            stock_media_kg_cost = li.balance / (total_weight_before + total_weight_after) * 2

            # Distribución analítica proporcional:
            products_before = moves_before.product_id
            products_after = moves_after.product_id
            products = products_before + products_after
            for product in products:
                total_product_weight_before = 0
                total_product_weight_after  = 0

                product_moves_before = self.env['stock.move.line'].search([
                    ('id', 'in', moves_before.ids),
                    ('product_id', '=', product.id),
                ])
                for move_line in product_moves_before:
                    # Multiplicar la cantidad por el peso del producto.
                    move_weight = move_line.qty_done * move_line.product_id.weight
                    # Sumar o restar el peso según la dirección del movimiento.
                    if move_line.location_id.usage == 'internal':
                        total_product_weight_before -= move_weight
                    if move_line.location_dest_id.usage == 'internal':
                        total_product_weight_before += move_weight

                product_moves_after = self.env['stock.move.line'].search([
                    ('id', 'in', moves_after.ids),
                    ('product_id', '=', product.id),
                ])
                for move_line in product_moves_after:
                    # Multiplicar la cantidad por el peso del producto.
                    move_weight = move_line.qty_done * move_line.product_id.weight
                    # Sumar o restar el peso según la dirección del movimiento.
                    if move_line.location_id.usage == 'internal':
                        total_product_weight_after -= move_weight
                    if move_line.location_dest_id.usage == 'internal':
                        total_product_weight_after += move_weight

                product_stock_cost = stock_media_kg_cost * (total_product_weight_before + total_product_weight_after) / 2

                # Buscamos si ya existe o se crea la cuenta analítica para este producto:
                analytic_account = self.check_or_create_analytic_account(product)

                # Creación del apunte analítico:
                product_field_id = self.env.company.product_field_id.name
                fixed_variable_field_id = self.env.company.fixed_variable_field_id.name
                department_field_id = self.env.company.department_field_id.name
                new_aal = self.env['account.analytic.line'].create({
                    'product_id': product.id,
                    'name': li.template_id.name + " - " + rec.name,
                    'amount': -1 * abs(product_stock_cost),
                    product_field_id: analytic_account.id,
                    fixed_variable_field_id: self.env.company.analytic_variable_account_id.id,
                    department_field_id: self.env.company.analytic_warehouse_department_id.id,
                    'analytic_distribution_id': self.id,
                    'analytic_distribution_template_id': li.template_id.id,
                })
