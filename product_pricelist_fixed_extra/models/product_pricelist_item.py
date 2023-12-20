from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    compute_price = fields.Selection(selection_add = [('fixed_extra', 'Fixed extra')],
                                     ondelete={'fixed_extra': 'set default'}
                                     )