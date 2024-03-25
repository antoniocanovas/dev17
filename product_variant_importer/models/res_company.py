# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    bom_attribute_id = fields.Many2one('product.attribute', string='Set attribute', store=True)
    size_attribute_id = fields.Many2one('product.attribute', string='Size attribute', store=True)
    color_attribute_id = fields.Many2one('product.attribute', string='Color attribute', store=True)
    single_prefix = fields.Char('Single prefix', store=True)
    single_sale = fields.Boolean('Enable pair sales', store=True, default=False)
    single_purchase = fields.Boolean('Enable pair purchase', store=True, default=False)
    exwork_currency_id = fields.Many2one('res.currency', store=True,
                                         default=lambda self: self.env.user.company_id.currency_id)