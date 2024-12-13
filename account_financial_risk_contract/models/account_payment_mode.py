from odoo import _, api, fields, models


class AccountPaymentMode(models.Model):
    _inherit = "account.payment.mode"

    is_confirming = fields.Boolean('Confirming', help='Is confirming')