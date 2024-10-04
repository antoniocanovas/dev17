# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api
from odoo.exceptions import UserError

class AnalyticDistribution(models.Model):
    _name = 'analytic.distribution'
    _description = 'Analytic distribution'

    name = fields.Char('Name', required=True)
    amount = fields.Float('Amount')
    compute_method = fields.Selection([('m1','Modo1'),('m2','Modo2')], string="Compute method")
    workcenter_ids = fields.Many2many('mrp.workcenter', string="Workcenters")
    date = fields.Date('Date')
    analytic_line_ids = fields.One2many('account.analytic.line', 'analytic_distribution_id', string='Analytic lines')
    comment = fields.Html('Comments', store=True, copy=False)

    income_account_ids = fields.Many2many(
        'account.account', string='Income accounts',
        relation='income_account_rel',
        column1='distribution_id',
        column2='account_id',
    )

    expense_account_ids = fields.Many2many(
        'account.account', string='Income accounts',
        relation='expense_account_rel',
        column1='distribution_id',
        column2='account_id',
    )

    def compute_distribution(self):
        if self.compute_method == "m1":
            raise UserError('modo 1')
        if self.compute_method == "m2":
            raise UserError('modo 2')