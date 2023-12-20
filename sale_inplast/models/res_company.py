# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


import logging

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    pnt_pricelist_day_lock = fields.Integer('Pricelist days lock', store=True, default=15)
    pnt_update_month_day = fields.Integer('Month day to update', store=True, default=1)
    pnt_plastic_tax = fields.Float('Plastic tax (€/kg)', default=0.45)