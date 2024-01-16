from odoo import _, api, fields, models
from datetime import date, datetime, timedelta

import logging
_logger = logging.getLogger(__name__)


class ProductPricelist(models.Model):
    _name = 'product.pricelist'
    _inherit = ['product.pricelist', 'mail.thread', 'mail.activity.mixin']

    # Campos para el impuesto del plástico:
    pnt_plastic_tax = fields.Boolean('Apply plastic tax', store=True, copy=False, default=True)
