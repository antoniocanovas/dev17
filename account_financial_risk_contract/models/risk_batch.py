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

    def _get_batch_risk_cost(self):
        amount = 0
        for li in self.invoice_ids:
            contract = self.env["risk.contract"].search(
                [("partner_id", "=", li.partner_id.id), ("state", "=", "done")],
                order="date_begin desc",
                limit=1,
            )
            if contract.id:
                amount += li.amount_untaxed_signed * (contract.margin / 100)
        self.insurance_amount = amount

    insurance_amount = fields.Monetary(
        "Insurance cost", store=False, copy=True, compute="_get_batch_risk_cost"
    )

    # NO FUNCIONA, NO SE ACTIVA (sería lo ideal y borrar el wizard):
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
