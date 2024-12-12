from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    risk_contract_ids = fields.One2many(
        "risk.contract", "partner_id", string="Risk contracts", store=True, copy=False
    )

    risk_sale_order_include = fields.Boolean(default=True)
    risk_invoice_draft_include = fields.Boolean(default=True)
    risk_invoice_open_include = fields.Boolean(default=True)
    risk_invoice_unpaid_include = fields.Boolean(default=True)
    risk_account_amount_include = fields.Boolean(default=True)
    risk_account_amount_unpaid_include = fields.Boolean(default=True)

    @api.depends("risk_contract_ids")
    def _get_risk_contract_len(self):
        self.risk_contract_count = len(self.risk_contract_ids.ids)

    risk_contract_count = fields.Integer(
        "Risk contracts", store=False, compute="_get_risk_contract_len"
    )
    risk_contract_id = fields.Many2one("risk.contract", string="Risk contract")
    risk_contract_description = fields.Text(
        "Notes", related="risk_contract_id.description"
    )
