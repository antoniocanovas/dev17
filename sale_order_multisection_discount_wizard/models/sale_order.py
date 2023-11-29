from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class SaleOrderInh(models.Model):
    _inherit = 'sale.order'






