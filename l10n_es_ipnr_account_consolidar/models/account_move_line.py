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
        "move_id.company_id.ipnr_enable",
        "move_id.ipnr_tax_zone",
        "move_id.fiscal_position_id",
        "move_id.fiscal_position_id.ipnr_subject",
    )
    def _compute_is_ipnr(self):
        for line in self:
            if line.display_type in ('line_section', 'line_note'):
                line.is_ipnr = False
                continue

            move = line.move_id
            if not move:
                line.is_ipnr = False
                continue

            company_enabled = move.company_id.ipnr_enable
            partner_in_zone = move.ipnr_tax_zone
            partner_shipping = move.partner_shipping_id
            fiscal_pos_ok = (
                (partner_shipping and partner_shipping.ipnr_dua_tax_zone) or
                not move.fiscal_position_id or
                move.fiscal_position_id.ipnr_subject
            )
            product_ok = (
                line.product_id and
                line.product_id.ipnr_subject in ("yes", "category") and
                line.product_id.tax_plastic_type in ("manufacturer", "acquirer")
            )
            line.is_ipnr = company_enabled and partner_in_zone and fiscal_pos_ok and product_ok


    def unlink(self):
        ipnr_invoices = self.mapped("move_id").filtered(
            lambda a: a.state == "draft" and a.is_ipnr and a.ipnr_is_date
        )
        res = super().unlink()
        if ipnr_invoices and not self.env.context.get("avoid_recursion"):
            ipnr_invoices.with_context(avoid_recursion=True)._delete_ipnr()
            ipnr_invoices.apply_ipnr()
        return res
