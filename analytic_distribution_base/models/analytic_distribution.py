# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api
from datetime import datetime
from odoo.exceptions import UserError

class AnalyticDistribution(models.Model):
    _name = 'analytic.distribution'
    _description = 'Analytic distribution'

    name = fields.Char('Name', required=True)
    amount = fields.Float('Amount', copy=False)
    compute_method = fields.Selection([('m1','Modo1'),('m2','Modo2')], string="Compute method")
#    workcenter_ids = fields.Many2many('mrp.workcenter', string="Workcenters")
    date_from = fields.Date('From date', copy=False)
    date_to = fields.Date('To date', copy=False, default=lambda self: datetime.today())
    analytic_line_ids = fields.One2many('account.analytic.line', 'analytic_distribution_id', string='Analytic lines')
    comment = fields.Html('Comments', store=True, copy=False)

    def _get_analytic_line_count(self):
        self.analytic_line_count = len(self.analytic_line_ids.ids)
    analytic_line_count = fields.Integer('Lines', compute='_get_analytic_line_count')

    income_credit  = fields.Monetary('Income credit')
    income_debit   = fields.Monetary('Income debit')
    expense_credit = fields.Monetary('Expense credit')
    expense_debit  = fields.Monetary('Expense debit')
    currency_id    = fields.Many2one('res.currency', default=lambda self: self.company.currency_id)

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
        datefrom = record.date_from
        dateto = record.date_to
        income_credit, income_debit, expense_credit, expense_debit = 0,0,0,0
        incomelines = self.env['account.move.line'].search(
            [('account_id', 'in', record.income_account_ids.ids), ('date', '>=', datefrom), ('date', '<=', dateto)])
        income_debit, income_credit = 0, 0
        for li in incomelines:
            income_debit += li.debit
            income_credit += li.credit

        expenselines = self.env['account.move.line'].search(
            [('account_id', 'in', record.expense_account_ids.ids), ('date', '>=', datefrom), ('date', '<=', dateto)])
        expense_debit, expense_credit = 0, 0
        for li in expenselines:
            expense_debit += li.debit
            expense_credit += li.credit

        self.write(
            {'income_debit':income_debit, 'income_credit':income_credit,
             'expense_debit':expense_debit, 'expense_credit':expense_credit})