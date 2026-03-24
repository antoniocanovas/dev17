# -*- coding: utf-8 -*-
# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models


class AnalyticDistribution(models.Model):
    _inherit = 'analytic.distribution'

    def compute_r1(self, li):
        for rec in self:
            pickings = rec.picking_in_handles_ids
            moves = self.env['stock.move'].search([
                ('picking_id','in',pickings.ids),
                ('product_id.mrp_bom_template_id.type', 'in',['pallet','pallet_nonmrp']),
                ('product_id.categ_id.type','=', 'handle' ),
                ('product_uom_qty', '>', 0),
            ])
            products = moves.product_id.pnt_parent_id
            # Para realizar un sólo apunte por producto base:
            for product in products:
                picking_cost = 0
                lines = moves.filtered(lambda l: l.product_id.pnt_parent_id == product)
                product_pickings = lines.picking_id
                # Para el reparto proporcional por albarán:
                for picking in product_pickings:
                    # Total de pallets a descargar (de todos los modelos de asas y de este en particular):
                    handles_lines = picking.move_ids_without_package.filtered(
                        lambda l: l.product_id.categ_id.type == 'handle'
                                  and l.product_id.pnt_product_type == 'packing'
                    )
                    product_lines = picking.move_ids_without_package.filtered(
                        lambda l: l.product_id.categ_id.type == 'handle'
                                  and l.product_id.pnt_product_type == 'packing'
                                  and l.product_id.pnt_parent_id == product
                    )
                    # Proporción del coste en función del nº de pallets del producto:
                    total_picking_pallets = sum(handles_lines.mapped('product_uom_qty'))
                    product_picking_pallets = sum(product_lines.mapped('product_uom_qty'))
                    picking_time = rec.picking_unload * (product_picking_pallets / total_picking_pallets)
                    picking_cost += picking_time * li.picking_hour_cost

                # Buscamos si ya existe o se crea la cuenta analítica para este producto:
                analytic_account = self.check_or_create_analytic_account(product)
                # Creación del apunte analítico:
                product_field_id = self.env.company.product_field_id.name
                fixed_variable_field_id = self.env.company.fixed_variable_field_id.name
                department_field_id = self.env.company.department_field_id.name
                machine_field_id = self.env.company.machine_field_id.name
                warehouse_dept = self.env.company.analytic_warehouse_department_id
                # Albaranes correspondientes al apunte analítico:
                picking_names = "[ "
                for picking in product_pickings:
                    picking_names += picking.name + " "
                picking_names += "]"

                # El campo 'product_id' en account.analytic.line espera un ID de 'product.product' (variante),
                # pero la lógica agrupa por 'product.template' (producto base).
                # Usamos la primera variante encontrada en las líneas de movimiento para satisfacer la restricción.
                product_variant_id = lines[0].product_id.id if lines else False

                new_aal = self.env['account.analytic.line'].create({
                    'product_id': product_variant_id,
                    'name': li.template_id.name + " - " + rec.name + " " + picking_names,
                    'amount': -1 * abs(picking_cost),
                    product_field_id: analytic_account.id,
                    fixed_variable_field_id: self.env.company.analytic_variable_account_id.id,
                    'analytic_distribution_id': self.id,
                    'analytic_distribution_template_id': li.template_id.id,
                })
