# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "ipnr.mixin"]

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
        for rec in self:
            rec.is_ipnr = any(line.is_ipnr for line in rec.order_line)

    @api.depends("is_ipnr", "date_order", "company_id")
    def _compute_ipnr_is_date(self):
        return super()._compute_ipnr_is_date()

    @api.depends("order_line")
    def _compute_ipnr_has_line(self):
        return super()._compute_ipnr_has_line()

    @api.depends("company_id")
    def _compute_company_ipnr(self):
        return super()._compute_company_ipnr()

    def _get_ipnr_line_vals(self, lines=False, **kwargs):
        ipnr_vals = super()._get_ipnr_line_vals(lines, **kwargs)
        ipnr_vals["order_id"] = self.id
        if self.order_line:
            ipnr_vals["sequence"] = self.order_line[-1].sequence + 1
        return ipnr_vals

    def apply_ipnr(self):
        """Delete and recreate IPNR lines (one per product line with IPNR).
        For confirmed orders, update existing lines in place to avoid unlink errors."""
        if self.env.context.get("avoid_recursion"):
            return
        ctx = {**self.env.context, "avoid_recursion": True}

        confirmed = self.filtered(lambda o: o.state in ("sale", "done"))
        editable = self - confirmed

        # Editable orders: delete and recreate as usual
        if editable:
            editable.with_context(ctx)._delete_ipnr()
            for rec in editable:
                lines_to_process = rec.order_line.filtered("is_ipnr")
                for line in lines_to_process:
                    ipnr_vals = rec._get_ipnr_line_vals(line)
                    qty_field = line._ipnr_secondary_unit_fields["qty_field"]
                    if ipnr_vals.get(qty_field, 0) > 0:
                        self.env["sale.order.line"].with_context(ctx).create(ipnr_vals)

        # Confirmed orders: update in place, zero out excess, create if needed
        for rec in confirmed:
            ipnr_product = self.env.ref(
                "l10n_es_ipnr_account.aportacion_ipnr_product_template",
                raise_if_not_found=False,
            )
            if not ipnr_product:
                continue
            existing_ipnr_lines = rec.order_line.filtered(
                lambda l: l.product_id == ipnr_product
            )
            lines_to_process = rec.order_line.filtered("is_ipnr")
            qty_field = "product_uom_qty"
            new_vals_list = []
            for line in lines_to_process:
                ipnr_vals = rec._get_ipnr_line_vals(line)
                if ipnr_vals.get(qty_field, 0) > 0:
                    new_vals_list.append(ipnr_vals)
            # Update or zero-out existing IPNR lines
            for i, existing_line in enumerate(existing_ipnr_lines):
                if i < len(new_vals_list):
                    existing_line.with_context(ctx).write({
                        qty_field: new_vals_list[i][qty_field],
                        "price_unit": new_vals_list[i]["price_unit"],
                    })
                else:
                    existing_line.with_context(ctx).write({qty_field: 0})
            # Create any additional IPNR lines not covered by existing ones
            for i in range(len(existing_ipnr_lines), len(new_vals_list)):
                self.env["sale.order.line"].with_context(ctx).create(new_vals_list[i])

    def write(self, vals):
        res = super().write(vals)
        # Check if a recomputation is needed
        if "order_line" in vals:
            self.apply_ipnr()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        sales = super().create(vals_list)
        for sale in sales.filtered("is_ipnr"):
            sale.apply_ipnr()
        return sales
