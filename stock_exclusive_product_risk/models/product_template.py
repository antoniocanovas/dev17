from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    partner_requesting_id = fields.Many2one('res.partner',string='Partner requesting')
