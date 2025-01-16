# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api

class ProductTemplate(models.Model):
    _inherit = "product.template"

    def create_default_product_stock_putaway_rule(self):
        for record in self:
            if (record.detailed_type == "product") and (record.product_variant_ids.ids) and (self.env.company.default_stock_putaway_rule_id.id):
                product = record.product_variant_ids[0]
                product_rules = self.env['stock.putaway.rule'].search([('product_id','=',product.id)])
                if not product_rules.ids:
                    rule = self.env.company.default_stock_putaway_rule_id
                    if record.categ_id.default_stock_putaway_rule_id.id:
                        rule = record.categ_id.default_stock_putaway_rule_id
                    self.env['stock.putaway.rule'].create({
                        'product_id': product.id,
                        'location_in_id': rule.location_in_id.id,
                        'location_out_id': rule.location_out_id.id,
                        'storage_category_id': rule.storage_category_id.id,
                        'package_type_ids': [(6,0,rule.package_type_ids.ids)],
                        'company_id': self.env.company.id,
                    })
