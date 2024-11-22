# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class PurchaseOrderLine(models.Model):
    _name = "purchase.order.line"
    _inherit = ["purchase.order.line", "ipnr.line.mixin"]

    _ipnr_secondary_unit_fields = {
        "parent_id": "order_id",
        "date_field": "date_order",
        "qty_field": "product_qty",
        "uom_field": "product_uom",
        "invoice_lines_field": "invoice_lines",
    }

    def _prepare_account_move_line(self, move=False):
        """Transfer IPNR value from POL to invoice."""
        res = super()._prepare_account_move_line(move)
        res["is_ipnr"] = self.is_ipnr
        return res

    def recompute_ipnr_from_lines(self):
        not_ipnr_lines = self.filtered(lambda a: not a.is_ipnr)
        if not_ipnr_lines:
            not_ipnr_lines.mapped("order_id").filtered(
                lambda a: any(
                    line.product_id.ipnr_has_amount
                    for line in a.order_line.filtered("product_id")
                )
            ).apply_ipnr()

    @api.model_create_multi
    def create(self, vals_list):
        recompute_ipnr = True
        if self.env.context.get("avoid_recursion"):
            recompute_ipnr = False
        lines = super(
            PurchaseOrderLine, self.with_context(avoid_recursion=True)
        ).create(vals_list)
        if recompute_ipnr:
            lines.recompute_ipnr_from_lines()
        return lines

    def write(self, values):
        recompute_ipnr = True
        if self.env.context.get("avoid_recursion"):
            recompute_ipnr = False
        ret = super(PurchaseOrderLine, self.with_context(avoid_recursion=True)).write(
            values
        )
        if recompute_ipnr and (
            "product_id" in values or "product_qty" in values or "product_uom" in values
        ):
            self.recompute_ipnr_from_lines()
        return ret
