from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    section_id = fields.Many2one('sale.order.line', readonly=True)

    # Reports hidden price line fields:
    hide_subtotal_section   = fields.Boolean('Hide subtotal', store=True, readonly=False)
    hide_subtotal_line      = fields.Boolean('Hide price', store=False, related='section_id.hide_subtotal_section')


