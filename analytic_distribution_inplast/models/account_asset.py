# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    account_asset_code = fields.Char(related='account_asset_id.code', string='Asset Account Code')
    machine_id = fields.Many2one(
        'account.analytic.account',
        string='Cuenta analítica (máquina/molde)',
        help='Para activos de maquinaria: cuenta del plan de máquinas (workcenter_id).\n'
             'Para activos de utillaje: cuenta del plan de equipos (equipment_id).'
    )