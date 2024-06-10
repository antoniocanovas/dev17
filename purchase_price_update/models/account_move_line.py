# -*- coding: utf-8 -*-

from odoo import models, api


class AccountMove(models.Model):
    _inherit = 'account.move'


    price_update_mode = fields.Selection(selection=[('0','0'),('1','1'),('2','2')], string='PUM', default='0')
