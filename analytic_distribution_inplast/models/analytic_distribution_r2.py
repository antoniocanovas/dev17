# -*- coding: utf-8 -*-
# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models


class AnalyticDistribution(models.Model):
    _inherit = 'analytic.distribution'

    def compute_r2(self, li):
        for rec in self:
            pickings = rec.picking_mrp2stock_ids
            moves = self.env['stock.move'].search([
                ('id','in',pickings.move_ids_without_package.ids),
                ('product_id.mrp_bom_template_id.type', '=','pallet'),
            ])
            products = moves.product_id.pnt_parent_id
            # Para realizar un sólo apunte por producto base:
            for product in products:
                lines = moves.filtered(lambda l: l.product_id.pnt_parent_id == product)
                product_pickings = lines.picking_id
                total_pallets = sum(lines.mapped('product_uom_qty'))
                picking_names = "[ "
                for picking in product_pickings:
                    picking_names += picking.name + " "
                picking_names += "]"
                picking_cost = total_pallets * li.picking_hour_cost * rec.pallet_reloc / 60
                # Buscamos si ya existe o se crea la cuenta analítica para este producto:
                analytic_account = self.check_or_create_analytic_account(product)
                # Creamos el apunte analítico:
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
