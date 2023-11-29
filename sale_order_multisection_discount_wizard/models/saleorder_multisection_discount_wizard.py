from odoo import _, api, fields, models

TYPE = [
    ('services', 'Final price applying discounts on services'),
    ('discount', 'Discount'),
]


class SaleOrderMultisectionDiscountWizard(models.TransientModel):
    _name = 'saleorder.multisection.discount.wizard'
    _description = 'Wizard SaleOrder Multisection Discount'

    #Campos con duda
    name = fields.Char('Name')
    #Campos
    discount = fields.Float('Discount')
    childs = fields.Boolean('Childs')
    products = fields.Boolean('Products')
    services = fields.Boolean('Services')
    all_quotation = fields.Boolean('All Quotation')
    price = fields.Float('Price')
    sale_id = fields.Many2one('sale.order')
    type = fields.Selection(selection=TYPE, string="Type")
    section_id = fields.Many2one('sale.order.line', string='Section')



