# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    active = fields.Boolean("Active", default=True)

    @api.depends("product_id")
    def _compute_product_customer_code(self):
        """Override to use commercial_partner_id instead of order_partner_id"""
        for line in self:
            if line.product_id:
                supplierinfo = line.product_id._select_customerinfo(
                    partner=line.order_partner_id.commercial_partner_id
                )
                code = supplierinfo.product_code
            else:
                code = ""
            line.product_customer_code = code

    def _compute_name(self):
        """Override to use commercial_partner_id instead of order_partner_id"""
        empty_lines = self.filtered(lambda x: not x.product_id)
        super(SaleOrderLine, empty_lines)._compute_name()
        for item in self - empty_lines:
            customerinfo = item.product_id._select_customerinfo(
                partner=item.order_partner_id.commercial_partner_id
            )
            if customerinfo.product_code:
                # Avoid to put the standard internal reference
                item = item.with_context(display_default_code=False)
            super(SaleOrderLine, item)._compute_name()
            if customerinfo.product_code:
                item.name = f"{item.name}"
        return

    @api.onchange("product_id")
    def _onchange_product_id_warning(self):
        """Override to use commercial_partner_id instead of order_partner_id"""
        res = super()._onchange_product_id_warning()
        for line in self:
            if line.product_id:
                customerinfo = line.product_id._select_customerinfo(
                    partner=line.order_partner_id.commercial_partner_id
                )
                if customerinfo.min_qty:
                    line.product_uom_qty = customerinfo.min_qty
        return res
