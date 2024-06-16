# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api

TYPE = [
    ('supplier','Supplier'),
    ('rent','Rent'),
    ('tax','Tax'),
    ('payroll','Payroll'),
    ('financing','Financing'),
    ('other','Other')
]

class PaymentEstimation(models.Model):
    _name = 'payment.estimation'
    _description = 'Payment estimations'

    name = fields.Char('Name')
    type = fields.Selection(selection=TYPE, string="Type", default='supplier')
    date = fields.Date('Date')
    amount = fields.Monetary('Amount')
    active = fields.Boolean('Active')
    currency_id = fields.Many2one('res.currency', default=1)
