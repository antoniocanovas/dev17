# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    analytic_distribution_id = fields.Many2one('analytic.distribution', string='Analytic distribution')
