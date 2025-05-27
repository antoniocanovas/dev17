# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


import logging

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    fsc_format_attribute_id = fields.Many2one(
        "product.attribute",
        string="Format attribute",
        store=True,
        help="FSC format attribute to be selected in products (W5.2, W7.1, etc)",
    )
