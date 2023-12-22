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
    pnt_update_month_day = fields.Integer('Pricelist update day', store=True, default=1)
    pnt_plastic_tax = fields.Float('Plastics tax (€/kg)', store=True, default=0.45, digits='Product Price',
                                   help='Tasa de impuesto por kg de plástico no reciclabe fabricado en España o importado.'
                                        ' Es recuperable si es vendido fuera de España')
