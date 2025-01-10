# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api

class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    product_id = fields.Many2one('product.product', string='Distribution Product')
    categ_id = fields.Many2one('product.category', string='Distribution Category')
    department_id = fields.Many2one('hr.department', string='Distribution department')