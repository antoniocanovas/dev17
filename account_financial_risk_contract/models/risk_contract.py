from odoo import _, api, fields, models
from datetime import date
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)

STATE = [
    ("draft", "Draft"),
    ("waiting", "Waiting"),
    ("done", "Done"),
    ("refused", "Refused"),
]


class RiskContract(models.Model):
    _name = "risk.contract"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Risk Contracts"

    name = fields.Char(string="Contract", store=True, tracking=100)
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        store=True,
        copy=True,
        required=True,
        tracking=100,
    )
    date_begin = fields.Date("Date begin", store=True, copy=False, tracking=100)
    date_end = fields.Date("Date end", store=True, copy=False, tracking=100)
    risk_level = fields.Char("Risk level", store=True, copy=True, tracking=100)
    coverage = fields.Float("Coverage", store=True, copy=True, tracking=100)
    supplier_id = fields.Many2one(
        "res.partner",
        string="Supplier",
        store=True,
        copy=True,
        required=True,
        tracking=100,
    )
    demand = fields.Monetary("Demand", store=True, copy=True, required=True)
    amount = fields.Monetary("Amount", store=True, copy=True, tracking=100)
    internal_risk = fields.Monetary("Internal", store=True, copy=True, tracking=100)
    currency_id = fields.Many2one("res.currency", required=True, default=lambda self: self.env.company.currency_id)
    active = fields.Boolean(
        "Active", store=True, copy=False, default=True, tracking=100
    )
    state = fields.Selection(
        selection=STATE,
        string="State",
        store=True,
        copy=False,
        default="draft",
        tracking=100,
    )
    description = fields.Text("Notes", store=True, copy=False)
    margin = fields.Float("Supplier margin (%)", store=True, copy=True)
    claim = fields.Integer("Claim period (days)", store=True, copy=True)

    # Plus contract:
    plus = fields.Boolean('Plus option',
                          help='Enables you to extend coverage under conditions other than the original for the extended amount.')
    plus_amount = fields.Monetary("Plus amount", store=True, copy=True, tracking=100)
    plus_margin = fields.Float("Plus margin (%)", store=True, copy=True)

    def update_risk_partner(self):
        for record in self:
            partner = record.partner_id
            if record.date_end and record.date_end < date.today():
                raise UserError("Expiration date must be after today")
            else:
                amount = record.amount + record.internal_risk
                if record.plus: amount += record.plus_amount
                partner.write({"credit_limit": amount, "risk_contract_id": record.id})

    _sql_constraints = [('unique_risk_contract_name', 'unique(name)', "This code already exists")]
