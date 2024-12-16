from odoo import models, fields


class AccountMove(models.Model):
    _inherit = "account.move"

    referrer_plan_ids = fields.One2many('referrer.plan.rel', 'invoice_id', string='Referrers')
