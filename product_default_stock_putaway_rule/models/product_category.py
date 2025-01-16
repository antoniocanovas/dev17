# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api


class ProductCategory(models.Model):
    _inherit = "product.category"

    default_stock_putaway_rule_id = fields.Many2one('stock.putaway.rule', string='Default stock rule')
