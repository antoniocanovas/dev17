# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.tools import frozendict


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "ipnr.mixin"]

    _ipnr_secondary_unit_fields = {
        "line_ids": "order_line",
        "date_field": "date_order",
        "editable_states": ["draft", "sent"],
    }

    @api.depends("company_id", "fiscal_position_id")
    def _compute_is_ipnr(self):
        return super()._compute_is_ipnr()

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
        for rec in self.filtered(
            lambda a: a.is_ipnr and a.ipnr_is_date and a.state in ["draft", "sent"]
        ):
            ipnr_vals = rec._get_ipnr_line_vals()
            self.env["sale.order.line"].create(ipnr_vals)

    def write(self, vals):
        res = super().write(vals)
        ipnr_sales = self.filtered(
            lambda a: a.is_ipnr
            and a.ipnr_is_date
            and any(
                line.product_id.ipnr_has_amount
                for line in a.order_line.filtered("product_id")
            )
        )
        for sale in ipnr_sales.filtered("id"):
            if self.env.context.get("avoid_recursion"):
                continue
            sale.automatic_ipnr_exception()
            sale.with_context(avoid_recursion=True).apply_ipnr()
            sale.env.context = frozendict(
                {**sale.env.context, "avoid_recursion": False}
            )
        (self - ipnr_sales).filtered(
            lambda a: (
                not a.is_ipnr
                or not any(
                    line.product_id.ipnr_has_amount
                    for line in a.order_line.filtered("product_id")
                )
            )
            and a.ipnr_has_line
        )._delete_ipnr()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        sales = super().create(vals_list)
        for sale in sales.filtered(
            lambda a: a.is_ipnr
            and a.ipnr_is_date
            and any(
                line.product_id.ipnr_has_amount
                for line in a.order_line.filtered("product_id")
            )
        ):
            sale.automatic_ipnr_exception()
            sale.apply_ipnr()
        return sales
