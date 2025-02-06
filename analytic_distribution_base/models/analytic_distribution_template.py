# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api
from datetime import datetime
from odoo.exceptions import UserError

class AnalyticDistributionTemplate(models.Model):
    _name = 'analytic.distribution.template'
    _description = 'Analytic distribution templates'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char('Name', required=True)
    amount = fields.Float('Amount', copy=False)
    compute_method = fields.Selection([('demo','Demo')], string="Compute method")
    analytic_line_ids = fields.One2many('account.analytic.line', 'analytic_distribution_template_id', string='Analytic lines')
    comment = fields.Html('Comments', store=True, copy=False)

    def _get_analytic_line_count(self):
        self.analytic_line_count = len(self.analytic_line_ids.ids)
    analytic_line_count = fields.Integer('Lines', compute='_get_analytic_line_count')

    currency_id    = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    income_account_ids = fields.Many2many(
        'account.account', string='Income accounts',
        relation='income_account_rel',
        column1='distribution_id',
        column2='account_id',
    )

    expense_account_ids = fields.Many2many(
        'account.account', string='Expense accounts',
        relation='expense_account_rel',
        column1='distribution_id',
        column2='account_id',
    )

    income_analytic_ids = fields.Many2many(
        'account.analytic.account', string='Analytics income',
        relation='income_analytic_account_rel',
        column1='distribution_id',
        column2='analytic_account_id',
    )

    expense_analytic_ids = fields.Many2many(
        'account.analytic.account', string='Analytics expense',
        relation='expense_analytic_account_rel',
        column1='distribution_id',
        column2='analytic_account_id',
    )
