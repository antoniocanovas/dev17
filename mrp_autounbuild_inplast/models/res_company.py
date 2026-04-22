# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    auto_unbuild_mode = fields.Selection(
        selection=[
            ('lot', 'Lote'),
            ('serial_number', 'Número de serie'),
        ],
        string='Modo autounbuild',
        default='lot',
        help=(
            'Al estar seleccionado lote, la función autounbuild descompondrá un palet en sus cajas '
            'y estas tendrán un lote común con el mismo nombre que el del palet. '
            'Si está seleccionado serial el tratamiento de las cajas desmontadas será con su '
            'número de serie por caja en el modo lotepadre.01, lotepadre.02, ...'
        ),
    )
