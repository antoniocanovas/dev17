# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from odoo import SUPERUSER_ID, fields, models


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
        self.filtered(
            lambda a: a.state in self._ipnr_secondary_unit_fields["editable_states"]
        ).mapped(self._ipnr_secondary_unit_fields["line_ids"]).filtered(
            lambda b: b.is_ipnr
        ).unlink()

    def _get_ipnr_line_vals(self, lines=False, **kwargs):
        self.ensure_one()
        ipnr_vals = dict()
        ipnr_product_id = self.env.ref(
            "l10n_es_ipnr_account.aportacion_ipnr_product_template"
        )
        ipnr_vals["product_id"] = ipnr_product_id.id
        kg_uom_id = self.env.ref("uom.product_uom_kgm")
        ipnr_vals[
            self[
                self._ipnr_secondary_unit_fields["line_ids"]
            ]._ipnr_secondary_unit_fields["uom_field"]
        ] = kg_uom_id.id
        date = False
        ipnr_lines = (
            lines
            if lines
            else self[self._ipnr_secondary_unit_fields["line_ids"]].filtered(
                lambda a: a.product_id and a.product_id.ipnr_has_amount
            )
        )
        if self._name == "account.move":
            # Get a default date to calculate the ipnr amount when the
            # ipnr line is newly generated
            date = self.ipnr_default_date(ipnr_lines)
        else:
            date = self[self._ipnr_secondary_unit_fields["date_field"]]
        price = self.env["l10n.es.ipnr.amount"].get_ipnr_amount(date)
        # if model isn't account.move we delete the ipnr line
        invoice_lines = []
        if self._name != "account.move":
            ipnr_line_delete = self[
                self._ipnr_secondary_unit_fields["line_ids"]
            ].filtered(lambda a: a.product_id == ipnr_product_id)
            if (
                ipnr_line_delete
                and ipnr_line_delete[
                    ipnr_line_delete._ipnr_secondary_unit_fields[
                        "invoice_lines_field"
                    ]
                ]
            ):
                invoice_lines = ipnr_line_delete[
                    ipnr_line_delete._ipnr_secondary_unit_fields[
                        "invoice_lines_field"
                    ]
                ].ids
            ipnr_line_delete.unlink()
        weight = sum(
            line[
                self[
                    self._ipnr_secondary_unit_fields["line_ids"]
                ]._ipnr_secondary_unit_fields["uom_field"]
            ]._compute_quantity(
                line[line._ipnr_secondary_unit_fields["qty_field"]],
                line.product_id.uom_id,
            )
            * line.product_id.plastic_weight_non_recyclable
            for line in ipnr_lines
        )
        ipnr_vals.update(
            {
                self[
                    self._ipnr_secondary_unit_fields["line_ids"]
                ]._ipnr_secondary_unit_fields["qty_field"]: weight,
                "price_unit": price,
                "is_ipnr": True,
            }
        )
        if invoice_lines:
            ipnr_vals.update(
                {
                    self[
                        self._ipnr_secondary_unit_fields["line_ids"]
                    ]._ipnr_secondary_unit_fields[
                        "invoice_lines_field"
                    ]: invoice_lines
                }
            )
        if self._name == "account.move":
            ipnr_vals["move_id"] = self.id
        return ipnr_vals

    def automatic_ipnr_exception(self):
        self.ensure_one()
        products_without_weight = (
            self[self._ipnr_secondary_unit_fields["line_ids"]]
            .mapped("product_id")
            .filtered(lambda a: a.ipnr_has_amount and a.plastic_weight_non_recyclable <= 0.0 and a.plastic_tax_weight <= 0.0)
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
