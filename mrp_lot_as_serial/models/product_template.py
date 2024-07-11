# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    pnt_mrp_as_serial = fields.Boolean('MRP serial', default=False)