# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api

class AnalyticDistribution(models.Model):
    _name = 'analytic.distribution'
    _description = 'Analytic distribution'

    name = fields.Char('Name', store=True)
    income_account_ids = fields.Many2many('account.account', string='Income accounts')
#    expense_account_ids = fields.Many2many('account.account', string='Expense accounts')
    compute_method = fields.Selection([('m1','Modo1'),('m2','Modo2')], string="Compute method")
    workcenter_ids = fields.Many2many('mrp.workcenter', string="Workcenters")
    date = fields.Date('Date')
    analytic_line_ids = fields.One2many('account.analytic.line', 'analytic_distribution_id', string='Analytic lines')
    comment = fields.Html('Comments', store=True, copy=False)
