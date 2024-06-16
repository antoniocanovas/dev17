# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api

class PaymentEstimation(models.Model):
    _name = 'payment.estimation'
    _description = 'Payment estimations'

    name = fields.Char('Name')
    date = fields.Date('Date')
    amount = fields.Monetary('Amount')
    active = fields.Boolean('Active')
    currency_id = fields.Many2one('res.currency', default=1)
