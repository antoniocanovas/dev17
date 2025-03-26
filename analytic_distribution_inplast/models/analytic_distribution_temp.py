# -*- coding: utf-8 -*-
# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from docutils.nodes import container
from odoo import fields, models, api
from odoo.exceptions import UserError


class AnalyticDistribution(models.Model):
    _inherit = 'analytic.distribution'


    ###########################################
    # R3.1: Desubicación y carga: Se miran los albaranes de salida (no utilizan playa) de Tapones y asas.
    # El coste es calculado por el precio por minuto.
# PDTE REVISAR: caps_handle_picking_load = (rec.sale_caps_picking_qty + rec.sale_handles_picking_qty) * rec.pallet_reloc / 60
    ###########################################
    def compute_r31(self, li):
        for rec in self:
            moves = self.env['stock.move'].search([
                ('picking_id.date_done', '>=', rec.date_from),
                ('picking_id.date_done', '<=', rec.date_to),
                ('picking_id.picking_type_code', '=', 'outgoing'),
                ('state', 'in', ['done']),
                ('product_id.mrp_bom_template_id.type', 'in', ['pallet', 'pallet_nonmrp']),
                ('product_uom_qty', '>', 0),
            ])
            pickings = moves.picking_id
            products = moves.product_id.pnt_parent_id
            for product in products:
                lines = moves.filtered(lambda l: l.product_id.pnt_parent_id == product)
                total_pallets = sum(lines.mapped('product_uom_qty'))
                picking_cost = total_pallets * li.picking_hour_cost / 60 * rec.pallet_reloc
                # Buscamos si ya existe o se crea la cuenta analítica para este producto:
                analytic_account = self.check_or_create_analytic_account(product.pnt_parent_id)
                product_field_id = self.env.company.product_field_id.name
                fixed_variable_field_id = self.env.company.fixed_variable_field_id.name
                department_field_id = self.env.company.department_field_id.name

                new_aal = self.env['account.analytic.line'].create({
                    'product_id': product.pnt_parent_id.id,
                    'name': li.template_id.name + " - " rec.name,
                    'amount': - picking_cost,
                    product_field_id: analytic_account.id,
                    fixed_variable_field_id: self.env.company.analytic_variable_account_id.id,
                    department_field_id: self.env.company.analytic_warehouse_department_id.id,
                    'analytic_distribution_id': self.id,
                    'analytic_distribution_template_id': li.template_id.id,
                })
