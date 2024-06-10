# -*- coding: utf-8 -*-

from odoo import models, api, fields


class AccountMove(models.Model):
    _inherit = 'account.move.line'


    is_purchase = fields.Boolean('Is purchase', compute='_get_is_purchase')
