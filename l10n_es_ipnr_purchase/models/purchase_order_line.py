# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


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

    is_ipnr = fields.Boolean(
        compute="_compute_is_ipnr",
        store=True,
        readonly=False,
    )

    @api.depends(
        "product_id",
        "product_id.ipnr_subject",
        "product_id.tax_plastic_type",
        "order_id.company_id.ipnr_enable",
        "order_id.dest_address_id.ipnr_tax_zone",
        "order_id.partner_id.country_id",
    )
    def _compute_is_ipnr(self):
        for line in self:
            order = line.order_id
            if not order:
                line.is_ipnr = False
                continue

            company_enabled = order.company_id.ipnr_enable
            # Check if partner is from Spain
            partner_is_spain = order.partner_id.country_id.code == 'ES' if order.partner_id.country_id else False

            # Determine tax zone based on dropship or normal purchase
            picking_type = order.picking_type_id
            if picking_type and picking_type.code == 'dropship':
                dest_address = order.dest_address_id
                in_tax_zone = dest_address.ipnr_tax_zone if dest_address else False
            else:
                warehouse_partner = picking_type.warehouse_id.partner_id if picking_type and picking_type.warehouse_id else False
                in_tax_zone = warehouse_partner.ipnr_tax_zone if warehouse_partner else False

            product_ok = (
                line.product_id and
                line.product_id.ipnr_subject in ("yes", "category") and
                line.product_id.tax_plastic_type in ("manufacturer", "acquirer")
            )

            line.is_ipnr = company_enabled and partner_is_spain and in_tax_zone and product_ok

    def _prepare_account_move_line(self, move=False):
        """Transfer IPNR value from POL to invoice."""
        res = super()._prepare_account_move_line(move)
        res["is_ipnr"] = self.is_ipnr
        return res
