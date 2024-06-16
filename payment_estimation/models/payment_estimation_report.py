# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api

class PaymentEstimationReport(models.Model):
    _name = 'payment.estimation.report'
    _description = 'Payment estimations report'

    name = fields.Char('Name')
    from_date = fields.Date('From date', required=True, default='2000-01-01')
    to_date = fields.Date('To date', required=True)
    invoice_amount = fields.Monetary('Invoices amount')
    estimate_amount = fields.Monetary('Estimations amount')
    total_amount = fields.Monetary('Total')
    active = fields.Boolean('Active', default=True)
    currency_id = fields.Many2one('res.currency', default=1)

    @api.depends('to_date','from_date')
    def _get_move_ids(self):
        for record in self:
            invoices = self.env['account.move'].search([
                ('move_type','in',['in_invoice','in_refund']),
                ('state','=','posted'),
                ('payment_state','!=','paid')
            ])
            record['move_ids'] = [(6,0,invoices.ids)]
    move_ids = fields.Many2many('account.move', string='Invoices', compute='_get_move_ids')

    @api.depends('to_date','from_date')
    def _get_estimation_ids(self):
        for record in self:
            estimations = self.env['payment.estimation'].search([
                ('id','>', 1)
            ])
            record['estimation_ids'] = [(6,0,estimations.ids)]
    estimation_ids = fields.Many2many('payment.estimation', string='Estimations', compute='_get_estimation_ids')
