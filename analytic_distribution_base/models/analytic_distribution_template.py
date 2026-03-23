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

    enable_income = fields.Boolean(string='Enable income', default=False)
    income_domain = fields.Char(
        string='Income domain',
        default='[]',
        help='Dominio sobre account.move.line para seleccionar las líneas de ingreso. '
             'El filtro de fechas y estado (posted) se aplica automáticamente.',
    )
    enable_expense = fields.Boolean(string='Enable expense', default=False)
    expense_domain = fields.Char(
        string='Expense domain',
        default='[]',
        help='Dominio sobre account.move.line para seleccionar las líneas de gasto. '
             'El filtro de fechas y estado (posted) se aplica automáticamente.',
    )
