# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api

class PaymentEstimationReport(models.Model):
    _name = 'payment.estimation.report'
    _description = 'Payment estimations report'

    name = fields.Char('Name')
    from_date = fields.Date('From date', required=True, default='2000-01-01')
    to_date = fields.Date('To date', required=True)
    active = fields.Boolean('Active', default=True)
    currency_id = fields.Many2one('res.currency', default=1)

    @api.depends('to_date','from_date')
    def _get_move_line_ids(self):
        for record in self:
            aml = self.env['account.move.line'].search([
                ('account_id.code','in',['400000','410000']),
                ('parent_state','=','posted'),
                ('amount_residual','!=',0)
            ])
            record['move_ids'] = [(6,0,aml.ids)]
    move_ids = fields.Many2many('account.move.line', string='Invoices', compute='_get_move_line_ids')

    @api.depends('to_date','from_date')
    def _get_estimation_ids(self):
        for record in self:
            estimations = self.env['payment.estimation'].search([
                ('id','>', 1)
            ])
            record['estimation_ids'] = [(6,0,estimations.ids)]
    estimation_ids = fields.Many2many('payment.estimation', string='Estimations', compute='_get_estimation_ids')

    @api.depends('to_date','from_date')
    def _get_amount_residual(self):
        for record in self:
            total = 0
            for li in record.move_ids:
                total += li.amount_residual
            record['amount_residual'] = total
    amount_residual = fields.Monetary('Invoices amount', compute='_get_amount_residual')

    @api.depends('estimation_ids')
    def _get_estimation_total(self):
        for record in self:
            total = 0
            for li in record.estimation_ids:
                total += li.amount
            record['estimate_amount'] = total
    estimate_amount = fields.Monetary('Estimations amount', compute='_get_estimation_total')

    @api.depends('amount_residual','estimate_amount')
    def _get_total_amount(self):
        for record in self:
            record['total_amount'] = record.amount_residual + record.estimate_amount
    total_amount = fields.Monetary('Total', compute='_get_total_amount')
