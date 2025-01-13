# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'


    fixed_analytic_distribution = fields.Boolean(
        string='Fixed Analytic',
        help='Active will be fixed distribution, variable if not.')

    analytic_distribution_account_id = fields.Many2one(
        'account.analytic.account', string='Department',
        help='Analytic distribution account')
    @api.depends('name')
    def _get_analytic_distribution_plan(self):
        self.analytic_distribution_plan_id = self.env.company.analytic_distribution_plan_id.id
    analytic_distribution_plan_id = fields.Many2one('account.analytic.plan', string='Distribution plan',
                                                    compute='_get_analytic_distribution_plan')

    workcenter_id = fields.Many2one('mrp.workcenter', string='Workcenter')