# -*- coding: utf-8 -*-
# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models


class AnalyticDistribution(models.Model):
    _inherit = 'analytic.distribution'

    def compute_r5(self, li):
        for rec in self:
            # No hay tiempos diarios para 'raw_cistern','raw_sack',
            categ_types = ['raw_pallet', 'raw_bag', 'raw_cardboard', 'raw_color']
            types = [
                #                ['raw_cistern',rec.raw_cistern_reloc_daily],
                #                ['raw_sack',rec.raw_sack_reloc_daily],
                ['raw_pallet', rec.raw_pallet_reloc_daily],
                ['raw_bag', rec.raw_bag_reloc_daily],
                ['raw_cardboard', rec.raw_cboard_reloc_daily],
                ['raw_color', rec.raw_color_reloc_daily],
            ]

            # Recorremos los tipos posibles de encontrar, con su estimacion de tiempos por tipo según la tabla anterior:
            for type in types:
                moves = self.env['stock.move'].search([
                    ('date', '>=', rec.date_from),
                    ('date', '<=', rec.date_to),
                    ('location_dest_id.usage', '=', 'production'),  # Destino es una ubicación de producción
                    ('location_id.usage', '!=', 'production'),  # Origen no es una ubicación de producción
                    ('product_id.categ_id.type', '=', type[0]),  # Tipos de familia del producto
                    ('state', '=', 'done'),  # Albarán en estado "done"
                    ('product_uom_qty', '>', 0),
                ])

                # Suma de kg total por tipo de materia prima para después hacer reparto proporcional:
                # total_weight = sum(moves.mapped('product_uom_qty')) NO HACE FALTA ESTE, SINO EL DEL POR TIPO.

                # El tiempo es estimado por tipo de producto, así que hay que recorrer por tipo:
                for type in types:
                    type_moves = self.env['stock.move'].search([
                        ('id', 'in', moves.ids),
                        ('product_id.categ_id.type', '=', type[0]),
                    ])
                    type_weight = sum(type_moves.mapped('product_uom_qty'))

                    # Recorremos por producto para hacer un único apunte R4 por cada cuenta analítica:
                    products = type_moves.product_id
                    for product in products:
                        product_moves = self.env['stock.move'].search([
                            ('id', 'in', type_moves.ids),
                            ('product_id', '=', product.id),
                        ])

                        # Reparto proporcional por si un albarán lleva varios productos [len(picking_moves)]
                        product_weight = sum(product_moves.mapped('product_uom_qty'))
                        picking_cost = (product_weight / type_weight) * li.picking_hour_cost * (type[1] * rec.days)
                        # Nombre del apunte analítico:
                        mrp_names = "[ "
                        for ref in product_moves: mrp_names += ref.reference + " "
                        mrp_names += "]"

                        # Buscamos si ya existe o se crea la cuenta analítica para este producto:
                        analytic_account = self.check_or_create_analytic_account(product)

                        # Creación del apunte analítico:
                        product_field_id = self.env.company.product_field_id.name
                        fixed_variable_field_id = self.env.company.fixed_variable_field_id.name
                        department_field_id = self.env.company.department_field_id.name
                        warehouse_dept = self.env.company.analytic_warehouse_department_id
                        new_aal = self.env['account.analytic.line'].create({
                            'product_id': product.id,
                            'name': li.template_id.name + " - " + rec.name + " " + mrp_names,
                            'amount': -1 * abs(picking_cost),
                            'date': self.date_to,
                            product_field_id: analytic_account.id,
                            fixed_variable_field_id: self.env.company.analytic_variable_account_id.id,
                            'analytic_distribution_id': self.id,
                            'analytic_distribution_template_id': li.template_id.id,
                        })
