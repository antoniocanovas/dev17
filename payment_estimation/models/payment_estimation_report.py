# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api

class PaymentEstimationReport(models.Model):
    _name = 'payment.estimation.report'
    _description = 'Payment estimations report'

    name = fields.Char('Name')
    from_date = fields.Date('From date', required=True, default='2000-01-01')
    to_date = fields.Date('To date', required=True)
    customer_invoice = fields.Boolean('Customer invoices', default=True)
    active = fields.Boolean('Active', default=True)
    currency_id = fields.Many2one('res.currency', default=1)

    @api.depends('to_date','from_date')
    def _get_supplier_move_line_ids(self):
        for record in self:
            aml = self.env['account.move.line'].search([
                ('account_root_id','in',['40','41']),
                ('move_type', 'in', ['in_invoice', 'in_refund']),
                ('parent_state','=','posted'),
                ('amount_residual','!=',0),
                ('date_maturity', '>=', record.from_date),
                ('date_maturity', '<=', record.to_date),
            ])
            record['supplier_move_ids'] = [(6,0,aml.ids)]
    supplier_move_ids = fields.Many2many('account.move.line', string='Supplier Invoices', compute='_get_supplier_move_line_ids')

    @api.depends('to_date','from_date')
    def _get_customer_move_line_ids(self):
        for record in self:
            aml = self.env['account.move.line'].search([
                ('account_root_id','in',['43']),
                ('move_type', 'in', ['out_invoice', 'out_refund']),
                ('parent_state','=','posted'),
                ('amount_residual','!=',0),
                ('date_maturity', '>=', record.from_date),
                ('date_maturity', '<=', record.to_date),
            ])
            record['customer_move_ids'] = [(6,0,aml.ids)]
    customer_move_ids = fields.Many2many('account.move.line', string='Customer Invoices', compute='_get_customer_move_line_ids')


    @api.depends('to_date','from_date')
    def _get_estimation_ids(self):
        for record in self:
            estimations = self.env['payment.estimation'].search([
                ('date', '>=', record.from_date),
                ('date', '<=', record.to_date),
            ])
            record['estimation_ids'] = [(6,0,estimations.ids)]
    estimation_ids = fields.Many2many('payment.estimation', string='Estimations', compute='_get_estimation_ids')

    @api.depends('to_date','from_date')
    def _get_supplier_amount_residual(self):
        for record in self:
            total = 0
            for li in record.supplier_move_ids:
                total += li.amount_residual
            record['supplier_amount_residual'] = total
    supplier_amount_residual = fields.Monetary('Supplier amount', compute='_get_supplier_amount_residual')

    @api.depends('to_date','from_date')
    def _get_customer_amount_residual(self):
        for record in self:
            total = 0
            for li in record.customer_move_ids:
                total += li.amount_residual
            record['customer_amount_residual'] = total
    customer_amount_residual = fields.Monetary('Customer amount', compute='_get_customer_amount_residual')

    @api.depends('estimation_ids')
    def _get_estimation_total(self):
        for record in self:
            total = 0
            for li in record.estimation_ids:
                total += li.amount
            record['estimate_amount'] = total
    estimate_amount = fields.Monetary('Estimations amount', compute='_get_estimation_total')

    @api.depends('supplier_amount_residual','customer_amount_residual','estimate_amount')
    def _get_total_amount(self):
        for record in self:
            total = record.supplier_amount_residual + record.estimate_amount
            if record.customer_invoice:
                total += record.customer_amount_residual
            record['total_amount'] = total
    total_amount = fields.Monetary('Total', compute='_get_total_amount')
