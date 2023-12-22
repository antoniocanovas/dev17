from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    pnt_move_plastic_tax_id = fields.Many2many('account.move', store=True, string='Plastic tax entry')
