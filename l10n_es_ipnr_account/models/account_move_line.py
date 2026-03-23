# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _name = "account.move.line"
    _inherit = ["account.move.line", "ipnr.line.mixin"]

    _ipnr_secondary_unit_fields = {
        "parent_id": "move_id",
        "date_field": "date",
        "qty_field": "quantity",
        "uom_field": "product_uom_id",
    }

    is_ipnr = fields.Boolean(
        compute="_compute_is_ipnr",
        store=True,
        readonly=False,
    )

    @api.depends(
        "product_id",
        "product_id.ipnr_subject",
        "product_id.tax_plastic_type",
        "move_id.partner_id",
        "move_id.ipnr_tax_zone",
    )
    def _compute_is_ipnr(self):
        for line in self:
            if line.display_type in ('line_section', 'line_note'):
                line.is_ipnr = False
                continue
            product_ok = (
                line.product_id and
                line.product_id.ipnr_subject in ("yes", "category") and
                line.product_id.tax_plastic_type in ("manufacturer", "acquirer")
            )
            partner_in_zone = line.move_id.ipnr_tax_zone
            line.is_ipnr = bool(product_ok and partner_in_zone)


    def unlink(self):
        ipnr_invoices = self.mapped("move_id").filtered(
            lambda a: a.state == "draft" and a.is_ipnr and a.ipnr_is_date
        )
        res = super().unlink()
        if ipnr_invoices and not self.env.context.get("avoid_recursion"):
            ipnr_invoices.with_context(avoid_recursion=True)._delete_ipnr()
            ipnr_invoices.apply_ipnr()
        return res
