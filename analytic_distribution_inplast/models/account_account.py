# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api

class AccountAccount(models.Model):
    _inherit = 'account.account'

    fixed_analytic_distribution = fields.Boolean(
        'account.account',
        string='Fixed Analytic',
        help='Active will be fixed distribution, variable if not.')
