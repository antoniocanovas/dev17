# -*- coding: utf-8 -*-
# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models
from datetime import datetime, timedelta


class AnalyticDistribution(models.Model):
    _inherit = 'analytic.distribution'

    def compute_r7(self, li):
        for rec in self:
            bom_templates = ['pallet', 'pallet_nonmrp']
            today = datetime.today()
            products_packing = self.env['product.product'].search([
                ('detailed_type', '=', 'product'),
                ('mrp_bom_template_id.type', 'in', bom_templates),
            ])

            # Cálculo del total de jornadas para poder hacer la proporción:
            total_storages  = 0
            for ppack in products_packing:
                stock_before = ppack.with_context(to_date=rec.date_from).qty_available
                current_date = rec.date_from
                while current_date <= rec.date_to and current_date <= today:
                    stock_current_date = ppack.with_context(to_date=current_date).qty_available
                    total_storages += stock_current_date
                    current_date += timedelta(days=1)

            # Cálculo por producto base pararealizar la imputación analítica:
            products = products_packing.pnt_parent_id
            for product in products:
                storages = 0
                product_packings = self.env['product.product'].search([
                    ('id','in',products_packing.ids),
                    ('pnt_parent_id','=',product.id),
                ])
                for ppacking in product_packings:
                    stock_before = ppacking.with_context(to_date=rec.date_from).qty_available
                    current_date = rec.date_from
                    while current_date <= rec.date_to and current_date <= today:
                        stock_current_date = ppacking.with_context(to_date=current_date).qty_available
                        storages += stock_current_date
                        current_date += timedelta(days=1)

                # Buscamos si ya existe o se crea la cuenta analítica para este producto:
                analytic_account = self.check_or_create_analytic_account(product)
                # Creación del apunte analítico:
                product_field_id = self.env.company.product_field_id.name
                fixed_variable_field_id = self.env.company.fixed_variable_field_id.name
                department_field_id = self.env.company.department_field_id.name
                warehouse_dept = self.env.company.analytic_warehouse_department_id
                new_aal = self.env['account.analytic.line'].create({
                    'product_id': product.id,
                    'name': li.template_id.name + " - " + rec.name,
                    'amount': -1 * abs(li.balance * storages / total_storages),
                    'date': self.date_to,
                    product_field_id: analytic_account.id,
                    fixed_variable_field_id: self.env.company.analytic_variable_account_id.id,
                    'analytic_distribution_id': self.id,
                    'analytic_distribution_template_id': li.template_id.id,
                })
