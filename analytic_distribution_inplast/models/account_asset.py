# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    account_asset_code = fields.Char(related='account_asset_id.code', string='Asset Account Code')
    workcenter_id = fields.Many2one(
        'mrp.workcenter', string='Workcenter',
        help='Máquina utilizada para las distribuciones analíticas Inplast, sobre producto.'
    )
    equipment_id = fields.Many2one(
        'maintenance.equipment', string='Equipment',
        help='Molde o utensilio utilizado para las distribuciones analíticas Inplast, sobre producto.'
    )