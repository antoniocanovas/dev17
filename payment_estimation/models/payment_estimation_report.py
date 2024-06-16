# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api

class PaymentEstimationReport(models.Model):
    _name = 'payment.estimation.report'
    _description = 'Payment estimations report'

    name = fields.Char('Name')
    from_date = fields.Date('From date')
    to_date = fields.Date('To date')
    invoice_amount = fields.Monetary('Invoices amount')
    estimate_amount = fields.Monetary('Estimations amount')
    total_amount = fields.Monetary('Total')
    active = fields.Boolean('Active')
    currency_id = fields.Many2one('res.currency', default=1)

    move_ids = fields.Many2many('account.move', string='Invoices')
    estimation_ids = fields.Many2many('payment.estimation', string='Estimations')
