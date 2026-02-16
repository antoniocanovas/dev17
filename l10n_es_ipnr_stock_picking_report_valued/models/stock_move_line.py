# Copyright 2024 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    ipnr_amount_subtotal = fields.Monetary(
        compute="_compute_ipnr_amount", compute_sudo=True
    )
    ipnr_amount_tax = fields.Monetary(
        compute="_compute_ipnr_amount", compute_sudo=True
    )
    ipnr_amount_total = fields.Monetary(
        compute="_compute_ipnr_amount", compute_sudo=True
    )

    def _get_ipnr_product_taxes(self, ipnr_product):
        self.ensure_one()
        taxes = ipnr_product.taxes_id
        if not taxes:
            return False
        fiscal_position = self.sale_line.order_id.fiscal_position_id
        return fiscal_position.map_tax(taxes)

    def _get_ipnr_product_taxes_values(self, ipnr_product, price, qty):
        self.ensure_one()
        return self.env["account.tax"]._convert_to_tax_base_line_dict(
            self,
            partner=self.sale_line.order_partner_id,
            currency=self.currency_id,
            product=ipnr_product,
            taxes=self._get_ipnr_product_taxes(ipnr_product),
            price_unit=price,
            quantity=qty,
        )

    @api.depends("product_id", "date", "quantity")
    def _compute_ipnr_amount(self):
        for line in self:
            subtotal = 0.0
            tax_amount = 0.0
            total = 0.0
            if (
                line.product_id
                and line.sale_line
                and line.sale_line.order_id.is_ipnr
                and line.product_id.ipnr_has_amount
            ):
                ipnr_product_id = self.env.ref(
                    "l10n_es_ipnr_account.aportacion_ipnr_product_template"
                )
                price = self.env["l10n.es.ipnr.amount"].get_ipnr_amount(
                    line.sale_line.order_id.date_order
                )
                quantity = line._get_report_valued_quantity()
                weight = quantity * line.product_id.weight
                tax_results = self.env["account.tax"]._compute_taxes(
                    [
                        line._get_ipnr_product_taxes_values(
                            ipnr_product_id, price, weight
                        )
                    ]
                )
                totals = list(tax_results["totals"].values())[0]
                subtotal = totals["amount_untaxed"]
                tax_amount = totals["amount_tax"]
                total = subtotal + tax_amount
            line.ipnr_amount_subtotal = subtotal
            line.ipnr_amount_tax = tax_amount
            line.ipnr_amount_total = total
