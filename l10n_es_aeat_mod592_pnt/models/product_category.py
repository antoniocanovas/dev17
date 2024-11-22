from odoo import _, api, fields, models
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class ProductCategory(models.Model):
    _inherit = 'product.category'

    pnt_is_manufactured = fields.Boolean('Manufactured', store=True, copy=True, default=True,
                                         help='Enabled if products are manufactured, disabled when bought.')
    pnt_plastic_weight = fields.Float('Plastic weight', store=True, copy=True, digits='Stock Weight', tracking=True,
                                      help='Unit weight used to pricelist recalculation and plastic taxes.')
