# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


import logging

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    pnt_plastic_journal_id = fields.Many2one('account.journal', string='Plastic tax journal')
    pnt_plastic_tax = fields.Float('Plastics tax (€/kg)', store=True, default=0.45, digits='Product Price',
                                   help='Tasa de impuesto por kg de plástico no reciclabe fabricado en España o importado.'
                                        ' Es recuperable si es vendido fuera de España')
    pnt_plastic_commercial_account_id = fields.Many2one('account.account', string='Plastic Commercial',
                                                        help='Plastic AEAT account for commercial operations with plastic.')
    pnt_plastic_manufacture_account_id = fields.Many2one('account.account', string='Plastic Manufacture',
                                                         help='Plastic AEAT account for manufacturing plastics.')
