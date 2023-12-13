# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api

class WpSaleLine(models.Model):
    _name = 'wp.sale.line'
    _description = 'WP Sale line'

    product_id = fields.Many2one('product.product', store=True, copy=True)
    quantity = fields.Float('Quantity', store=True, copy=True)
    factor = fields.Float('Factor', store=True, copy=True)
    subtotal = fields.Monetary('Subtotal', store=True, copy=True)
    sale_id = fields.Many2one('sale.order', store=True, readonly=True, copy=False)
    currency_id = fields.Many2one('res.currency', store=True, default=1)

    @api.onchange('product_id')
    def get_wp_template_name(self):
        self.name = self.product_id.name
    name = fields.Char('name', store=True, required=True, compute='get_wp_template_name')
