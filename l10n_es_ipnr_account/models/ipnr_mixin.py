# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date
from typing import Any

from odoo import SUPERUSER_ID, _, fields, models
from odoo.exceptions import UserError


class IpnrMixin(models.AbstractModel):
    _name = "ipnr.mixin"
    _description = "Ipnr Mixin"

    is_ipnr = fields.Boolean(
        compute="_compute_is_ipnr",
        string="Subject to IPNR",
        store=True,
        readonly=False,
    )
    ipnr_is_date = fields.Boolean(
        compute="_compute_ipnr_is_date",
        store=True,
        help="Technical field to determine whether the date of a document subject to "
        "IPNR is equal or after the date selected in the company from which IPNR "
        "has to be applied.",
    )
    ipnr_has_line = fields.Boolean(compute="_compute_ipnr_has_line")
    # It cannot be a related field as ipnr.mixin does not have a company_id field
    ipnr_company = fields.Boolean(compute="_compute_ipnr_company")
    ipnr_automated_exception_id = fields.Many2one(
        comodel_name="mail.activity", readonly=True
    )

    _ipnr_secondary_unit_fields = {}

    def _compute_is_ipnr(self):
        for rec in self:
            rec.is_ipnr = rec.company_id.ipnr_enable and (
                not rec.fiscal_position_id or rec.fiscal_position_id.ipnr_subject
            )

    def _compute_ipnr_is_date(self):
        for rec in self:
            try:
                date = rec[rec._ipnr_secondary_unit_fields["date_field"]].date()
            except AttributeError:
                date = rec[rec._ipnr_secondary_unit_fields["date_field"]]
            rec.ipnr_is_date = (
                rec.is_ipnr and date and date >= rec.company_id.ipnr_date_from
            )

    def _compute_ipnr_has_line(self):
        for rec in self:
            rec.ipnr_has_line = any(
                line.is_ipnr
                for line in rec[rec._ipnr_secondary_unit_fields["line_ids"]]
            )

    def _compute_ipnr_company(self):
        for rec in self:
            rec.ipnr_company = rec.company_id.ipnr_enable

    def _delete_ipnr(self):
        """Delete the IPNR product line."""
        ipnr_product = self.env.ref(
            "l10n_es_ipnr_account.aportacion_ipnr_product_template",
            raise_if_not_found=False,
        )
        if not ipnr_product:
            return
        for rec in self:
            lines_to_delete = rec[
                rec._ipnr_secondary_unit_fields["line_ids"]
            ].filtered(lambda l: l.product_id == ipnr_product)
            lines_to_delete.unlink()

    def _get_ipnr_line_vals(self, line=False, **kwargs) -> dict:
        """
        Get the values for the IPNR tax line.
        If line is provided, calculate weight for that single line.
        If line is False, calculate total weight from all IPNR-applicable lines.
        Extra kwargs are passed through for subclass extensions.
        """
        self.ensure_one()
        ipnr_product = self.env.ref(
            "l10n_es_ipnr_account.aportacion_ipnr_product_template"
        )
        kg_uom = self.env.ref("uom.product_uom_kgm")

        # Security check for product configuration
        if ipnr_product.uom_id != kg_uom or ipnr_product.uom_po_id != kg_uom:
            raise UserError(
                _(
                    "The IPNR contribution product is misconfigured.\n\n"
                    "Please go to the product '%s' and ensure that "
                    "both 'Unit of Measure' and 'Purchase Unit of Measure' are set to 'kg'."
                )
                % ipnr_product.display_name
            )

        # Get line model and its field configuration
        all_lines = self[self._ipnr_secondary_unit_fields["line_ids"]]

        # Get date - use ipnr_default_date if available and date field is False
        ipnr_date = self[self._ipnr_secondary_unit_fields["date_field"]]
        if not ipnr_date and hasattr(self, 'ipnr_default_date'):
            ipnr_date = self.ipnr_default_date(all_lines)
        if not ipnr_date:
            ipnr_date = date.today()
        price = self.env["l10n.es.ipnr.amount"].get_ipnr_amount(ipnr_date)
        # Get field names from the line model (use first line or model default)
        if all_lines:
            line_fields = all_lines[0]._ipnr_secondary_unit_fields
        elif line:
            line_fields = line._ipnr_secondary_unit_fields
        else:
            # Fallback to account.move.line fields
            line_fields = {"uom_field": "product_uom_id", "qty_field": "quantity"}

        # Calculate weight
        if line:
            # Single line provided
            uom = line[line_fields["uom_field"]]
            qty = line[line_fields["qty_field"]]
            if uom and qty and line.product_id:
                weight = uom._compute_quantity(
                    qty, line.product_id.uom_id
                ) * line.product_id.plastic_weight_non_recyclable
            else:
                weight = 0.0
        else:
            # No line provided - calculate total from all IPNR lines
            ipnr_lines = all_lines.filtered(
                lambda l: l.product_id and l.product_id.ipnr_has_amount
            )
            weight = 0.0
            for ln in ipnr_lines:
                uom = ln[line_fields["uom_field"]]
                qty = ln[line_fields["qty_field"]]
                if uom and qty:
                    weight += uom._compute_quantity(
                        qty, ln.product_id.uom_id
                    ) * ln.product_id.plastic_weight_non_recyclable

        # Build vals with correct field names for the line model
        ipnr_vals = {
            "product_id": ipnr_product.id,
            line_fields["uom_field"]: kg_uom.id,
            line_fields["qty_field"]: weight,
            "price_unit": price,
            "sequence": 10000,
        }

        if self._name == "account.move":
            ipnr_vals["move_id"] = self.id

        return ipnr_vals

    def create_ipnr_line(self, lines, **kwargs):
        """Create an IPNR contribution line based on the given lines."""
        self.ensure_one()
        ctx = {**self.env.context, "avoid_recursion": True}
        ipnr_vals = self._get_ipnr_line_vals(**kwargs)

        # Get the line model name from the configuration
        line_ids_field = self._ipnr_secondary_unit_fields["line_ids"]
        line_model = self[line_ids_field]._name

        if ipnr_vals.get("quantity", ipnr_vals.get("product_uom_qty", 0)) > 0:
            return self.env[line_model].with_context(ctx).create(ipnr_vals)
        return self.env[line_model]

    def automatic_ipnr_exception(self):
        self.ensure_one()
        products_without_weight = (
            self[self._ipnr_secondary_unit_fields["line_ids"]]
            .mapped("product_id")
            .filtered(
                lambda a: a.ipnr_has_amount
                and a.plastic_weight_non_recyclable <= 0.0
                and a.plastic_tax_weight <= 0.0
            )
        )
        if products_without_weight:
            values = {
                "model": self._name,
                "origin": self.id,
                "products": products_without_weight,
            }
            note = self.env["ir.qweb"]._render(
                "l10n_es_ipnr_account.exception_ipnr", values
            )
            if not self.ipnr_automated_exception_id:
                odoobot_id = self.env.ref("base.partner_root").id
                activity = self.activity_schedule(
                    "mail.mail_activity_data_warning",
                    date.today(),
                    note=note,
                    user_id=self.user_id.id or SUPERUSER_ID,
                )
                activity.write(
                    {
                        "create_uid": odoobot_id,
                    }
                )
                self.write(
                    {
                        "ipnr_automated_exception_id": activity.id,
                    }
                )
            else:
                self.ipnr_automated_exception_id.write({"note": note})
