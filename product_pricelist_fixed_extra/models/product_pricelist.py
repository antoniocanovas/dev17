from odoo import _, api, fields, models
from datetime import date

import logging
_logger = logging.getLogger(__name__)


class ProductPricelist(models.Model):
    _name = 'product.pricelist'
    _inherit = ['product.pricelist', 'mail.thread', 'mail.activity.mixin']

    compute_price = fields.Selection(selection_add=[('fixed_extra', 'Fixed extra')])
