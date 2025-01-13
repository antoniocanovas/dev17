# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    analytic_distribution_account_id = fields.Many2one('account.analytic.account', string='Department',
                                                       help='Analytic distribution account')
    @api.depends('name')
    def _get_analytic_distribution_plan(self):
        self.analytic_distribution_plan_id = self.env.company.analytic_distribution_plan_id.id
    analytic_distribution_plan_id = fields.Many2one('account.analytic.plan', string='Distribution plan',
                                                    compute='_get_analytic_distribution_plan')



    # Eliminado tras reunión con Ibarra (enero 2025):
    #analytic_categ_plan_id = fields.Many2one('account.analytic.plan', string='Category')
    #analytic_department_plan_id = fields.Many2one('account.analytic.plan', string='Department')

    #analytic_spain_account_id = fields.Many2one('account.analytic.account', string='Spain account')
    #analytic_eu_account_id = fields.Many2one('account.analytic.account', string='Europe account')
    #analytic_non_eu_account_id = fields.Many2one('account.analytic.account', string='Non Europe account')