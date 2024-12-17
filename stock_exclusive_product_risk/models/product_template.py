from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    partner_requesting_id = fields.Many2one('res.partner',string='Partner requesting')
