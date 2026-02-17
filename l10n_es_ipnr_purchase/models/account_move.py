# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def ipnr_default_date(self, lines):
        self.ensure_one()
        date = super().ipnr_default_date(lines)
        if not self.invoice_date and lines.mapped("purchase_order_id"):
            date = lines.mapped("purchase_order_id")[0].date_order.date()
        return date
