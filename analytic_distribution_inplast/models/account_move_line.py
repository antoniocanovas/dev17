# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # Las ventas se asignan por defecto a Producción, asignación del valor parametrizado desde res.company:
    @api.depends('move_type')
    def _get_analytic_distribution_account(self):
        for record in self:
            analytic_account = False
            default_analytic_account = self.env.company.default_sale_analytic_distribution_account_id
            if record.move_id.move_type in ['out_invoice','out_refund']:
                analytic_account = default_analytic_account.id
            record['analytic_distribution_account_id'] = analytic_account
    analytic_distribution_account_id = fields.Many2one('account.analytic.account', string='Department',
                                                       readonly=False, store=True,
                                                       compute='_get_analytic_distribution_account',
                                                       help='Analytic distribution account',
                                                       )
    @api.depends('name')
    def _get_analytic_distribution_plan(self):
        self.analytic_distribution_plan_id = self.env.company.analytic_distribution_plan_id.id
    analytic_distribution_plan_id = fields.Many2one('account.analytic.plan', string='Distribution plan',
                                                    compute='_get_analytic_distribution_plan')
