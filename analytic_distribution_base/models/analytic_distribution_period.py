# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api
from datetime import datetime
from odoo.exceptions import UserError

class AnalyticDistribution(models.Model):
    _name = 'analytic.distribution.month'
    _description = 'Analytic distribution period'

    name = fields.Char('Name', required=True)
    date_from = fields.Date('From date', copy=False)
    date_to = fields.Date('To date', copy=False, default=lambda self: datetime.today())
    analytic_line_ids = fields.One2many('account.analytic.line', 'analytic_distribution_period_id', string='Analytic lines')
    comment = fields.Html('Comments', store=True, copy=False)

    analytic_distribution_ids = fields.Many2many('analytic.distribution', string='Distributions')
    def _get_analytic_line_count(self):
        self.analytic_line_count = len(self.analytic_line_ids.ids)
    analytic_line_count = fields.Integer('Lines', compute='_get_analytic_line_count')

    currency_id    = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
