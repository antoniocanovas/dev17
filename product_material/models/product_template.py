# Copyright Serincloud SL - Ingenieriacloud.com


from odoo import fields, models, api, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    material_id = fields.Many2one(
        "product.material", string="Material", copy=True, ondelete='restrict'
    )
