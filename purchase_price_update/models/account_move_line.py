# -*- coding: utf-8 -*-

from odoo import models, api, fields


class AccountMove(models.Model):
    _inherit = 'account.move.line'


    price_update_mode = fields.Selection([('0','0'),('1','1'),('2','2')], string='PUM', default='0')
    @api.depends('move_type')
    def _get_is_purchase(self):
        for record in self:
            purchase = False
            if record.move_type in ['in_invoice','in_refund']:
                purchase = True
            record['is_purchase'] = purchase
    is_purchase = fields.Boolean('Is purchase', compute='_get_is_purchase')
