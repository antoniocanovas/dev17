from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

import logging

_logger = logging.getLogger(__name__)

STATE = [
    ("draft", "Draft"),
    ("done", "Done"),
]


class RiskBatch(models.Model):
    _name = "risk.batch"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Risk invoices batch"

    name = fields.Char(string="Name", required=True, tracking=100)
    supplier_id = fields.Many2one(
        "res.partner", string="Supplier", store=True, copy=True, required=True
    )
    date = fields.Date("Date", store=True, copy=False, tracking=100)
    currency_id = fields.Many2one("res.currency", required=True, default=lambda self: self.env.company.currency_id)
    state = fields.Selection(
        selection=STATE,
        string="State",
        store=True,
        copy=False,
        default="draft",
        tracking=100,
    )
    description = fields.Text("Notes", store=True, copy=False)
    invoice_ids = fields.Many2many("account.move", store=True)
    vto = fields.Integer("Expiration", help="Expiration in days")

    def _get_invoices_net_amount(self):
        amount = 0
        for li in self.invoice_ids:
            amount += li.amount_untaxed_signed
        self.amount = amount

    amount = fields.Monetary(
        "Amount", store=False, copy=True, compute="_get_invoices_net_amount"
    )

    insurance_amount = fields.Monetary("Insurance cost")

    @api.constrains('state')
    def _check_and_compute_insurance_amount(self):
        for record in self:
            amount = 0
            if record.state == "done":
                customers = set()
                for li in record.invoice_ids:
                    customers.add(li.commercial_partner_id)

                for customer in customers:
                    # El cliente tiene riesgo con la empresa aseguradora de este lote:
                    if customer.risk_contract_id.supplier_id.id != record.supplier_id.id:
                        raise UserError('No available contract for ' + customer.name + ' with ' + record.supplier_id.name)

                    # Importe concedido en contrato de riesgo:
                    contract = customer.risk_contract_id
                    insurance_risk = contract.amount
                    if contract.plus:
                        insurance_risk += contract.plus_amount

                    # Riesgo de otros lotes de facturas ya enviadas:
                    unpaid_sent_invoices = self.env['account.move'].search(
                        [('commercial_partner_id', '=', customer.id), ('amount_total', '!=', 0),
                         ('risk_batch_id', '!=', False), ('risk_batch_id', '!=', record.id)])
                    customer_risk_sent = 0
                    for invoice in unpaid_sent_invoices:
                        customer_risk_sent += invoice.amount_total
                    # Riesgo disponible antes de validar este lote:
                    customer_risk_available = insurance_risk - customer_risk_sent

                    # Chequeo de riesgo disponible tras validar este lote:
                    customer_invoices = self.env['account.move'].search(
                        [('id', 'in', record.invoice_ids.ids), ('commercial_partner_id', '=', customer.id)])
                    additional_risk = 0
                    for li in customer_invoices:
                        additional_risk += li.amount_total
                    # Alerta de riesgo sobrepasado, o cálculo de coste estimado:
                    if additional_risk > customer_risk_available:
                        raise UserError(
                            'Customer ' + customer.name + ' exceeds contract risk, delete any invoice. Available risk: ' + str(
                                customer_risk_available) + ', this batch risk: ' + str(additional_risk))
                    else:
                        standard_pending_risk = contract.amount - customer_risk_sent

                        if standard_pending_risk > 0 and additional_risk < standard_pending_risk:
                            used_standard_risk = additional_risk
                            used_plus_risk = 0
                        elif standard_pending_risk > 0 and additional_risk > standard_pending_risk:
                            used_standard_risk = standard_pending_risk
                            used_plus_risk = additional_risk - standard_pending_risk
                        else:
                            used_standard_risk = 0
                            used_plus_risk = additional_risk

                        amount += used_standard_risk * contract.margin / 100 + used_plus_risk * contract.plus_margin / 100

            record['insurance_amount'] = amount

    # NO FUNCIONA el depends, NO SE ACTIVA (sería lo ideal y borrar el wizard):
    #    @api.depends('invoice_ids')
    def update_invoice_risk_batch_id(self):
        for record in self:
            invoices = self.env["account.move"].search(
                [
                    "|",
                    ("risk_batch_id", "=", record.id),
                    ("id", "in", record.invoice_ids.ids),
                ]
            )
            for li in invoices:
                if li.id not in record.invoice_ids.ids:
                    li["risk_batch_id"] = False
                else:
                    li["risk_batch_id"] = record.id
