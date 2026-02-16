# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def ipnr_default_date(self, lines):
        self.ensure_one()
        date = super().ipnr_default_date(lines)
        if not self.invoice_date and lines.mapped("sale_line_ids"):
            date = lines.mapped("sale_line_ids")[0].order_id.date_order.date()
        return date

    @api.model
    def modify_ipnr_line(self, ipnr_line, lines):
        weight = sum(
            line.product_uom_id._compute_quantity(line.quantity, line.product_id.uom_id)
            * line.product_id.plastic_weight_non_recyclable
            for line in lines
        )
        ipnr_line.write({"quantity": weight})

    def _get_ipnr_line_vals(self, lines=False, **kwargs):
        vals = super()._get_ipnr_line_vals(lines, **kwargs)
        if kwargs.get("sale_ipnr_line"):
            vals["sale_line_ids"] = [kwargs.get("sale_ipnr_line").id]
        return vals

    def manage_sale_ipnr_lines(self):
        ipnr_lines = self.invoice_line_ids.filtered(
            lambda a: a.is_ipnr and a.sale_line_ids
        )
        for ipnr_line in ipnr_lines:
            order_id = ipnr_line.sale_line_ids.order_id[0]
            lines_from_order = self.invoice_line_ids.filtered(
                lambda a: a.sale_line_ids.order_id == order_id
                and a.product_id
                and a.product_id.ipnr_has_amount
            )
            self.modify_ipnr_line(ipnr_line, lines_from_order)
        # In case IPNR Lines do not exist in the invoice
        # i.e. the line has been deleted in the invoice
        ipnr_lines_in_orders = self.invoice_line_ids.mapped(
            "sale_line_ids.order_id.order_line"
        ).filtered(lambda a: a.is_ipnr)
        not_used_ipnr_lines_in_orders = ipnr_lines_in_orders - ipnr_lines.mapped(
            "sale_line_ids"
        )
        for ipnr_line in not_used_ipnr_lines_in_orders:
            order_id = ipnr_line.order_id
            lines = self.invoice_line_ids.filtered(
                lambda a: a.sale_line_ids.order_id == order_id
                and a.product_id
                and a.product_id.ipnr_has_amount
            )
            if lines:
                self.create_ipnr_line(lines, **{"sale_ipnr_line": ipnr_line})
        ipnr_lines = self.invoice_line_ids.filtered(
            lambda a: a.is_ipnr and a.sale_line_ids
        )
        if len(ipnr_lines) > 1:
            for ipnr_line in ipnr_lines.filtered(
                lambda a: a.sale_line_ids.order_id.name not in a.name
            ):
                ipnr_line.write(
                    {
                        "name": "{}: {}".format(
                            ipnr_line.sale_line_ids.order_id.name,
                            ipnr_line.name,
                        )
                    }
                )

    @api.model
    def get_independent_invoice_lines_domain(self):
        domain = super().get_independent_invoice_lines_domain()
        domain += [("sale_line_ids", "=", False)]
        return domain

    def apply_ipnr(self):
        for rec in self.filtered(
            lambda a: a.is_ipnr
            and a.ipnr_is_date
            and a.move_type in ["out_invoice", "out_refund"]
        ):
            rec.manage_sale_ipnr_lines()
        ret = super().apply_ipnr()
        return ret

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        for move in moves:
            orders = move.line_ids.sale_line_ids.order_id.filtered(
                lambda a: a.is_ipnr
            )
            if orders:
                move.manage_sale_ipnr_lines()
        return moves
