from odoo import _, api, fields, models
from datetime import datetime

import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.depends('state', 'invoice_line_ids', 'pricelist_id.pnt_state')
    def _get_invoice_pricelist_state(self):
        for record in self:
            state = False
            if (record.move_type in ['out_invoice','out_refund']) and (record.state == 'draft'):
                state = record.pricelist_id.pnt_state
                if record.state in ['draft','sent']:
                    state = record.pricelist_id.pnt_state
            record['pnt_pricelist_state'] = state
    pnt_pricelist_state = fields.Selection([('active','Active'),('update','Update'),('locked','Locked')],
                                           string='Pricelist state', store=True, copy=False,
                                           compute='_get_invoice_pricelist_state')

    pnt_last_price_update = fields.Datetime('Last price update', default=lambda self: datetime.now())