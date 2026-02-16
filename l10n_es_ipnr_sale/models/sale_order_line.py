# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from typing import Any

from odoo import api, fields, models
from odoo.tools import float_compare


class SaleOrderLine(models.Model):
    _name = "sale.order.line"
    _inherit = ["sale.order.line", "ipnr.line.mixin"]

    _ipnr_secondary_unit_fields = {
        "parent_id": "order_id",
        "date_field": "date_order",
        "qty_field": "product_uom_qty",
        "uom_field": "product_uom",
        "invoice_lines_field": "invoice_lines",
    }

    is_ipnr = fields.Boolean(
        compute="_compute_is_ipnr",
        store=True,
        readonly=False,
    )

    @api.depends(
        "product_id",
        "product_id.ipnr_subject",
        "order_id.company_id.ipnr_enable",
        "order_id.partner_shipping_id.ipnr_tax_zone",
        "order_id.fiscal_position_id",
        "order_id.fiscal_position_id.ipnr_subject",
    )
    def _compute_is_ipnr(self):
        for line in self:
            order = line.order_id
            company_enabled = order.company_id.ipnr_enable
            partner_in_zone = order.partner_shipping_id.ipnr_tax_zone
            fiscal_pos_ok = ( order.partner_shipping_id.ipnr_dua_tax_zone or
                not order.fiscal_position_id or order.fiscal_position_id.ipnr_subject
            )
            product_ok = (
                line.product_id and line.product_id.ipnr_subject in ("yes", "category") and
                line.product_id.tax_plastic_type in ("manufacturer", "acquirer")
            )
            print(company_enabled)
            print(partner_in_zone)
            print(fiscal_pos_ok)
            print(product_ok)
            line.is_ipnr = company_enabled and partner_in_zone and fiscal_pos_ok and product_ok

    def _prepare_invoice_line(self, **optional_values: Any) -> dict:
        """Transfer IPNR value from SOL to invoice."""
        res = super()._prepare_invoice_line(**optional_values)
        res["is_ipnr"] = self.is_ipnr
        return res

    @api.depends("is_ipnr")
    def _compute_invoice_status(self) -> None:
        """Compute the invoice status of sale order lines."""
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        ipnr_lines = self.filtered("is_ipnr")
        for line in ipnr_lines:
            if (
                float_compare(
                    line.qty_invoiced, line.product_uom_qty, precision_digits=precision
                )
                >= 0
            ):
                line.invoice_status = "invoiced"
            else:
                line.invoice_status = "no"
        return super(SaleOrderLine, self - ipnr_lines)._compute_invoice_status()
