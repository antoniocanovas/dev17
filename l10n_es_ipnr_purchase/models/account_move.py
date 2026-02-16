# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def ipnr_default_date(self, lines):
        self.ensure_one()
        date = super().ipnr_default_date(lines)
        if not self.invoice_date and lines.mapped("purchase_order_id"):
            date = lines.mapped("purchase_order_id")[0].date_order.date()
        return date

    def _get_ipnr_line_vals(self, lines=False, **kwargs):
        vals = super()._get_ipnr_line_vals(lines, **kwargs)
        if kwargs.get("purchase_ipnr_line"):
            vals["purchase_line_id"] = kwargs.get("purchase_ipnr_line").id
        return vals

    @api.model
    def modify_ipnr_line(self, ipnr_line, lines):
        weight = sum(
            line.product_uom_id._compute_quantity(line.quantity, line.product_id.uom_id)
            * line.product_id.plastic_weight_non_recyclable
            for line in lines
        )
        ipnr_line.write({"quantity": weight})

    def manage_purchase_ipnr_lines(self, line_type=None):
        ipnr_lines = self.invoice_line_ids.filtered(
            lambda a: a.is_ipnr and a.purchase_order_id
        )
        for ipnr_line in ipnr_lines:
            order_id = ipnr_line.purchase_order_id
            lines_from_order = self.invoice_line_ids.filtered(
                lambda a: a.purchase_order_id == order_id
                and a.product_id
                and a.product_id.ipnr_has_amount
            )
            self.modify_ipnr_line(ipnr_line, lines_from_order)
        # In case Sigaus Lines do not exist in the invoice
        # i.e. the line has been deleted in the invoice
        ipnr_lines_in_orders = self.invoice_line_ids.mapped(
            "purchase_line_id.order_id.order_line"
        ).filtered(lambda a: a.is_ipnr)
        not_used_ipnr_lines_in_orders = ipnr_lines_in_orders - ipnr_lines.mapped(
            "purchase_line_id"
        )
        for ipnr_line in not_used_ipnr_lines_in_orders:
            order_id = ipnr_line.order_id
            lines = self.invoice_line_ids.filtered(
                lambda a: a.purchase_order_id == order_id
                and a.product_id
                and a.product_id.ipnr_has_amount
            )
            if lines:
                self.create_ipnr_line(lines, **{"purchase_ipnr_line": ipnr_line})
        ipnr_lines = self.invoice_line_ids.filtered(
            lambda a: a.is_ipnr and a.purchase_order_id
        )
        if len(ipnr_lines) > 1:
            for ipnr_line in ipnr_lines.filtered(
                lambda a: a.purchase_order_id.name not in a.name
            ):
                ipnr_line.write(
                    {
                        "name": "{}: {}".format(
                            ipnr_line.purchase_order_id.name,
                            ipnr_line.name,
                        )
                    }
                )

    @api.model
    def get_independent_invoice_lines_domain(self):
        domain = super().get_independent_invoice_lines_domain()
        domain += [("purchase_line_id", "=", False)]
        return domain

    def apply_ipnr(self):
        for rec in self.filtered(
            lambda a: a.is_ipnr
            and a.ipnr_is_date
            and a.move_type in ["in_invoice", "in_refund"]
        ):
            rec.manage_purchase_ipnr_lines()
        ret = super().apply_ipnr()
        return ret

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        if self.env.context.get("from_purchase"):
            moves.filtered(lambda a: a.is_ipnr).manage_purchase_ipnr_lines()
        return moves
