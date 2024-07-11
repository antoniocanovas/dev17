# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    pnt_mrp_packaging = fields.Boolean('MRP auto packaging', default=False)