from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class SaleOrderOption(models.Model):
    _inherit = 'sale.order.option'

    pnt_product_ids = fields.Many2many('product.product', store=False, string='Pricelist products',
                                   related='order_id.pricelist_id.pnt_product_ids')





