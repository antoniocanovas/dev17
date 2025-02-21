# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api
from datetime import datetime
from odoo.exceptions import UserError

class AnalyticDistributionLine(models.Model):
    _name = 'analytic.distribution.line'
    _description = 'Analytic distribution line'


    template_id = fields.Many2one('analytic.distribution.template', string='Template')
    name = fields.Char(related='template_id.name')
    distribution_id = fields.Many2one('analytic.distribution', string='Distribution')
    date_from = fields.Date(related='distribution_id.date_from')
    date_to = fields.Date(related='distribution_id.date_to')

    income_debit = fields.Monetary('Income debit')
    income_credit = fields.Monetary('Income credit')
    expense_debit = fields.Monetary('Expense debit')
    expense_credit = fields.Monetary('Expense credit')
    balance = fields.Monetary('Balance')

    currency_id = fields.Many2one('res.currency', default=lambda self:self.env.company.currency_id)


    def compute_debit_credit(self):
        for record in self:
            datefrom = record.date_from
            dateto = record.date_to
            income_credit, income_debit, expense_credit, expense_debit = 0,0,0,0
            incomelines = self.env['account.move.line'].search([
                ('account_id', 'in', record.template_id.income_account_ids.ids),
                ('date', '>=', datefrom),
                ('date', '<=', dateto),
                ('parent_state', 'in', ['posted']),
                ('analytic_account_ids', 'in', record.template_id.income_analytic_ids.ids),
            ])
            for li in incomelines:
                income_debit += li.debit
                income_credit += li.credit

            expenselines = self.env['account.move.line'].search([
                ('account_id', 'in', record.template_id.expense_account_ids.ids),
                ('date', '>=', datefrom),
                ('date', '<=', dateto),
                ('parent_state', 'in', ['posted']),
                ('analytic_account_ids', 'in', record.template_id.expense_analytic_ids.ids),
            ])
            for li in expenselines:
                expense_debit += li.debit
                expense_credit += li.credit

            balance = income_debit - income_credit - expense_debit + expense_credit

            record.write(
                {'income_debit':income_debit, 'income_credit':income_credit,
                 'expense_debit':expense_debit, 'expense_credit':expense_credit,
                 'balance':balance})
