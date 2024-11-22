# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.osv import expression


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "ipnr.mixin"]

    _ipnr_secondary_unit_fields = {
        "line_ids": "invoice_line_ids",
        "date_field": "invoice_date",
        "editable_states": [
            "draft",
        ],
    }

    @api.depends(
        "company_id",
        "fiscal_position_id",
        "move_type",
    )
    def _compute_is_ipnr(self):
        for rec in self:
            if rec.is_invoice():
                return super()._compute_is_ipnr()
            else:
                rec.is_ipnr = False

    @api.depends("is_ipnr", "invoice_date", "company_id")
    def _compute_ipnr_is_date(self):
        ret = super()._compute_ipnr_is_date()
        for rec in self.filtered(
            lambda a: a.is_ipnr
            and not a.invoice_date
            and a.company_id.ipnr_date_from
        ):
            rec.ipnr_is_date = (
                rec.create_date.date() >= rec.company_id.ipnr_date_from
            )
        return ret

    @api.depends("invoice_line_ids")
    def _compute_ipnr_has_line(self):
        return super()._compute_ipnr_has_line()

    @api.depends("company_id")
    def _compute_ipnr_company(self):
        return super()._compute_ipnr_company()

    def ipnr_default_date(self, lines):
        self.ensure_one()
        return self.invoice_date or self.create_date.date()

    @api.model
    def get_independent_invoice_lines_domain(self):
        """
        Override this method to get the invoice lines not related to other
        models (i.e. sale orders)
        """
        return []

    def manage_ipnr_invoice_lines(self):
        self.ensure_one()
        independent_lines_domain = self.get_independent_invoice_lines_domain()
        independent_ipnr_lines_domain = expression.AND(
            [
                [
                    ("move_id", "=", self.id),
                    ("is_ipnr", "=", True),
                ],
                independent_lines_domain,
            ]
        )
        self.env["account.move.line"].search(independent_ipnr_lines_domain).unlink()
        # Invoice lines not related to other documents (i.e. sales)
        independent_lines_domain = expression.AND(
            [
                [
                    ("move_id", "=", self.id),
                    ("product_id", "!=", False),
                    ("product_id.ipnr_has_amount", "=", True),
                ],
                independent_lines_domain,
            ]
        )
        independent_lines = self.env["account.move.line"].search(
            independent_lines_domain
        )
        if independent_lines:
            self.create_ipnr_line(independent_lines)

    def create_ipnr_line(self, lines, **kwargs):
        values = self._get_ipnr_line_vals(lines, **kwargs)
        self.env["account.move.line"].create(values)

    def apply_ipnr(self):
        for invoice in self.filtered(
            lambda a: a.state == "draft" and a.is_ipnr and a.ipnr_is_date and a.id
        ):
            invoice.automatic_ipnr_exception()
            invoice.with_context(avoid_recursion=True).manage_ipnr_invoice_lines()

    def write(self, vals):
        res = super().write(vals)
        if any(
            value in list(vals.keys())
            for value in [
                "is_ipnr",
                "company_id",
                "fiscal_position_id",
                "invoice_line_ids",
                "move_type",
                "invoice_date",
            ]
        ):
            self.with_context(avoid_recursion=True)._delete_ipnr()
            self.apply_ipnr()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        for move in moves.filtered(lambda a: a.is_ipnr and a.ipnr_is_date):
            move.automatic_ipnr_exception()
            move.apply_ipnr()
        return moves
