# -*- coding: utf-8 -*-
# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models


class AnalyticDistribution(models.Model):
    _inherit = 'analytic.distribution'

    def compute_r4(self, li):
        for rec in self:
            categ_types = ['raw_cistern', 'raw_sack', 'raw_pallet', 'raw_bag', 'raw_cardboard', 'raw_color']
            types = [
                ['raw_cistern', rec.raw_cistern_unload],
                ['raw_sack', rec.raw_sack_unload],
                ['raw_pallet', rec.raw_pallet_unload],
                ['raw_bag', rec.raw_bag_unload],
                ['raw_cardboard', rec.raw_cardboard_unload],
                ['raw_color', rec.raw_color_unload]
            ]
            # Recorremos los tipos posibles de encontrar, con su estimacion de tiempos por tipo según la tabla anterior:
            for type in types:
                moves = self.env['stock.move'].search([
                    ('picking_id.date_done', '>=', rec.date_from),
                    ('picking_id.date_done', '<=', rec.date_to),
                    ('picking_id.picking_type_code', '=', 'incoming'),
                    ('state', 'in', ['done']),
                    ('product_id.categ_id.type', '=', type[0]),
                    ('product_uom_qty', '>', 0),
                ])
                products = moves.product_id

                # Recorremos por producto para hacer un único apunte R4 por cada cuenta analítica:
                for product in products:
                    product_moves = self.env['stock.move'].search([
                        ('id', 'in', moves.ids),
                        ('product_id', '=', product.id),
                    ])
                    # este reparto está mal, hay que tener el importe estimado por días total del mes,

                    # Reparto proporcional por si un albarán lleva varios productos [len(picking_moves)]
                    product_pickings = product_moves.picking_id
                    picking_cost = 0
                    for pi in product_pickings:
                        picking_moves = self.env['stock.move'].search([
                            ('picking_id', '=', pi.id),
                            ('product_id.categ_id.type', 'in', categ_types),
                        ]).product_id
                        picking_cost += li.picking_hour_cost * type[1] / len(picking_moves)

                    # Nombre del apunte analítico:
                    picking_names = "[ "
                    for product_picking in product_pickings: picking_names += product_picking.name + " "
                    picking_names += "]"

                    # Buscamos si ya existe o se crea la cuenta analítica para este producto:
                    analytic_account = self.check_or_create_analytic_account(product)

                    # Creación del apunte analítico:
                    product_field_id = self.env.company.product_field_id.name
                    fixed_variable_field_id = self.env.company.fixed_variable_field_id.name
                    department_field_id = self.env.company.department_field_id.name
                    warehouse_dept = self.env.company.analytic_warehouse_department_id
                    new_aal = self.env['account.analytic.line'].create({
                        'product_id': product.id,
                        'name': li.template_id.name + " - " + rec.name + " " + picking_names,
                        'amount': -1 * abs(picking_cost),
                        product_field_id: analytic_account.id,
                        fixed_variable_field_id: self.env.company.analytic_variable_account_id.id,
                        'analytic_distribution_id': self.id,
                        'analytic_distribution_template_id': li.template_id.id,
                    })
