# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def ipnr_default_date(self, lines):
        self.ensure_one()
        date = super().ipnr_default_date(lines)
        if not self.invoice_date and lines.mapped("sale_line_ids"):
            date = lines.mapped("sale_line_ids")[0].order_id.date_order.date()
        return date
