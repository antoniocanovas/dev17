from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    pnt_tracking_date = fields.Date('Tracking date', store=True, copy=False)
    pnt_new_price = fields.Float('New price', store=True, copy=False, digits=(3,6))
    pnt_product_state = fields.Boolean('Active', related='product_tmpl_id.active', store=False)