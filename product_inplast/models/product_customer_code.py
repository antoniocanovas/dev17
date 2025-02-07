from odoo import fields, models, api


class ProductCustomerCode(models.Model):
    _name = "product.customer.code"
    _description = "Product Customer Code"

    name = fields.Char(string="Code", required=True)
    gtin = fields.Char(string="GTIN")
    partner_id = fields.Many2one('res.partner', string="Customer", required=True, domain="[('is_company', '=', True)]")
    product_tmpl_id = fields.Many2one('product.template', string="Product")