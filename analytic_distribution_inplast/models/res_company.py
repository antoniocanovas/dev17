# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    analytic_product_plan_id = fields.Many2one('account.analytic.plan', string='Product plan')
    analytic_distribution_plan_id = fields.Many2one('account.analytic.plan', string='Distribution plan')
    default_sale_analytic_distribution_account_id = fields.Many2one(
        'account.analytic.account',
        string='Sale department account',
        help='It will be used on customer invoice lines by default.'
    )


    # Eliminado tras reunión con Ibarra (enero 2025):
    #analytic_categ_plan_id = fields.Many2one('account.analytic.plan', string='Category')
    #analytic_department_plan_id = fields.Many2one('account.analytic.plan', string='Department')

    #analytic_spain_account_id = fields.Many2one('account.analytic.account', string='Spain account')
    #analytic_eu_account_id = fields.Many2one('account.analytic.account', string='Europe account')
    #analytic_non_eu_account_id = fields.Many2one('account.analytic.account', string='Non Europe account')