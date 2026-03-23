# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api
from odoo.tools.safe_eval import safe_eval


class AnalyticDistributionLine(models.Model):
    _name = 'analytic.distribution.line'
    _description = 'Analytic distribution line'

    template_id = fields.Many2one('analytic.distribution.template', string='Template')
    name = fields.Char(related='template_id.name')
    distribution_id = fields.Many2one('analytic.distribution', string='Distribution')
    date_from = fields.Datetime(related='distribution_id.date_from')
    date_to = fields.Datetime(related='distribution_id.date_to')

    income_debit = fields.Monetary('Income debit')
    income_credit = fields.Monetary('Income credit')
    expense_debit = fields.Monetary('Expense debit')
    expense_credit = fields.Monetary('Expense credit')
    balance = fields.Monetary('Balance')

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    # -------------------------------------------------------------------------
    # Helpers privados
    # -------------------------------------------------------------------------

    def _get_income_lines(self, extra_domain=None):
        """Devuelve los account.move.line de ingresos del periodo según el dominio del template."""
        if not self.template_id.enable_income:
            return self.env['account.move.line']
        domain = safe_eval(self.template_id.income_domain or '[]') + [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('parent_state', '=', 'posted'),
        ]
        if extra_domain:
            domain += extra_domain
        return self.env['account.move.line'].search(domain)

    def _get_expense_lines(self, extra_domain=None):
        """Devuelve los account.move.line de gastos del periodo según el dominio del template."""
        if not self.template_id.enable_expense:
            return self.env['account.move.line']
        domain = safe_eval(self.template_id.expense_domain or '[]') + [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('parent_state', '=', 'posted'),
        ]
        if extra_domain:
            domain += extra_domain
        return self.env['account.move.line'].search(domain)

    def _action_view_move_lines(self, name, line_ids):
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': 'account.move.line',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', line_ids)],
            'target': 'current',
        }

    # -------------------------------------------------------------------------
    # Acciones de navegación por campo
    # -------------------------------------------------------------------------

    def action_view_income_debit(self):
        self.ensure_one()
        return self._action_view_move_lines(
            f'{self.name} — Income Debit',
            self._get_income_lines([('debit', '>', 0)]).ids,
        )

    def action_view_income_credit(self):
        self.ensure_one()
        return self._action_view_move_lines(
            f'{self.name} — Income Credit',
            self._get_income_lines([('credit', '>', 0)]).ids,
        )

    def action_view_expense_debit(self):
        self.ensure_one()
        return self._action_view_move_lines(
            f'{self.name} — Expense Debit',
            self._get_expense_lines([('debit', '>', 0)]).ids,
        )

    def action_view_expense_credit(self):
        self.ensure_one()
        return self._action_view_move_lines(
            f'{self.name} — Expense Credit',
            self._get_expense_lines([('credit', '>', 0)]).ids,
        )

    def action_view_balance(self):
        self.ensure_one()
        ids = list(set(self._get_income_lines().ids + self._get_expense_lines().ids))
        return self._action_view_move_lines(f'{self.name} — Balance', ids)

    # -------------------------------------------------------------------------
    # Cálculo de importes
    # -------------------------------------------------------------------------

    def compute_debit_credit(self):
        for record in self:
            income_lines = record._get_income_lines()
            expense_lines = record._get_expense_lines()

            income_debit = sum(l.debit for l in income_lines)
            income_credit = sum(l.credit for l in income_lines)
            expense_debit = sum(l.debit for l in expense_lines)
            expense_credit = sum(l.credit for l in expense_lines)
            balance = income_debit - income_credit - expense_debit + expense_credit

            record.write({
                'income_debit': income_debit,
                'income_credit': income_credit,
                'expense_debit': expense_debit,
                'expense_credit': expense_credit,
                'balance': balance,
            })
