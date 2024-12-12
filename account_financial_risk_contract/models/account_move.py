from odoo import _, api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    risk_batch_id = fields.Many2one(
        "risk.batch", string="Risk batch", store=True, copy=False
    )
    credit_limit = fields.Float(related="partner_id.credit_limit")
