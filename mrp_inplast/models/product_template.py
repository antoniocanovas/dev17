# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    mrp_tool_ids = fields.One2many('mrp.product.tool', 'product_tmpl_id', string='Tools')