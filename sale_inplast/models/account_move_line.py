from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    pnt_product_ids = fields.Many2many('product.product', store=False, string='Pricelist products',
                                   related='move_id.pricelist_id.pnt_product_ids')

    pnt_product_type = fields.Selection(related="product_id.pnt_product_type")

    @api.onchange('quantity', 'product_id', 'product_packaging_id', 'product_packaging_qty')
    def _get_base_units(self):
        for li in self:
            qty = 0
            if (li.product_id.pnt_product_type == 'packing') and (li.product_id.pnt_parent_qty > 0):
                qty = li.quantity * li.product_id.pnt_parent_qty
            if (li.product_id.pnt_product_type == 'final'):
                qty = li.quantity
            li['pnt_base_qty'] = qty

    pnt_base_qty = fields.Integer('Base qty', store=False, compute='_get_base_units')

    @api.onchange('list_price', 'discount')
    def _get_1k_price(self):
        for record in self:
            price = record.price_unit * 1000
            if record.pnt_base_qty != 0:
                price = record.price_subtotal / record.pnt_base_qty * 1000
            record['pnt_base_1k_price'] = price

    pnt_base_1k_price = fields.Float('1K', compute='_get_1k_price')