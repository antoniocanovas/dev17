# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class PurchaseOrder(models.Model):
    _name = "purchase.order"
    _inherit = ["purchase.order", "ipnr.mixin"]

    _ipnr_secondary_unit_fields = {
        "line_ids": "order_line",
        "date_field": "date_order",
        "editable_states": ["draft", "sent"],
    }

    is_ipnr = fields.Boolean(
        string="Is IPNR",
        compute="_compute_is_ipnr",
        store=False,
    )

    @api.depends("order_line.is_ipnr")
    def _compute_is_ipnr(self):
        """Compute is_ipnr based on order lines (same philosophy as sales)."""
        for rec in self:
            rec.is_ipnr = any(line.is_ipnr for line in rec.order_line)

    @api.depends("is_ipnr", "date_order", "company_id")
    def _compute_ipnr_is_date(self):
        return super()._compute_ipnr_is_date()

    @api.depends("order_line")
    def _compute_ipnr_has_line(self):
        return super()._compute_ipnr_has_line()

    @api.depends("company_id")
    def _compute_ipnr_company(self):
        return super()._compute_ipnr_company()

    def _get_ipnr_line_vals(self, line=False, **kwargs):
        ipnr_vals = super()._get_ipnr_line_vals(line, **kwargs)
        ipnr_vals["order_id"] = self.id
        if self.order_line:
            ipnr_vals["sequence"] = self.order_line[-1].sequence + 1
        # Add date_planned for purchase order lines
        ipnr_vals["date_planned"] = (
            self.env["purchase.order.line"]
            ._get_date_planned(False)
            .strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        )
        return ipnr_vals

    def apply_ipnr(self):
        """Delete and recreate IPNR lines (one per product line with is_ipnr=True)."""
        if self.env.context.get("avoid_recursion"):
            return
        ctx = {**self.env.context, "avoid_recursion": True}
        self.with_context(ctx)._delete_ipnr()
        for rec in self:
            # Create one IPNR line per product line with is_ipnr=True
            lines_to_process = rec.order_line.filtered("is_ipnr")
            for line in lines_to_process:
                ipnr_vals = rec._get_ipnr_line_vals(line)
                qty_field = line._ipnr_secondary_unit_fields["qty_field"]
                if ipnr_vals.get(qty_field, 0) > 0:
                    self.env["purchase.order.line"].with_context(ctx).create(ipnr_vals)

    def action_create_invoice(self):
        obj = self.with_context(from_purchase=True)
        return super(PurchaseOrder, obj).action_create_invoice()

    def write(self, vals):
        res = super().write(vals)
        # Recalculate IPNR lines when order_line changes
        if "order_line" in vals:
            self.apply_ipnr()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        purchases = super().create(vals_list)
        for purchase in purchases.filtered("is_ipnr"):
            purchase.apply_ipnr()
        return purchases

    def copy(self, default=None):
        # Do not calculate IPNR through create method in purchase.order.lines
        # but calculate it through create method in purchase.order
        new_po = super(PurchaseOrder, self.with_context(avoid_recursion=True)).copy(
            default
        )
        return new_po
