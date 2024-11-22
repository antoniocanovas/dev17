# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMoveLine(models.Model):
    _name = "account.move.line"
    _inherit = ["account.move.line", "ipnr.line.mixin"]

    _ipnr_secondary_unit_fields = {
        "parent_id": "move_id",
        "date_field": "date",
        "qty_field": "quantity",
        "uom_field": "product_uom_id",
    }

    def unlink(self):
        ipnr_invoices = self.mapped("move_id").filtered(
            lambda a: a.state == "draft" and a.is_ipnr and a.ipnr_is_date
        )
        res = super().unlink()
        if ipnr_invoices and not self.env.context.get("avoid_recursion"):
            ipnr_invoices.with_context(avoid_recursion=True)._delete_ipnr()
            ipnr_invoices.apply_ipnr()
        return res
