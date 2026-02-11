# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class IpnrLineMixin(models.AbstractModel):
    _name = "ipnr.line.mixin"
    _description = "Ipnr Line Mixin"

    is_ipnr = fields.Boolean(copy=True, default=False)
    ipnr_amount = fields.Float(
        compute="_compute_ipnr_amount", digits="Product Price"
    )

    _ipnr_secondary_unit_fields = {}

    def _compute_ipnr_amount(self):
        for rec in self:
            ipnr_amount = 0.0
            if rec.product_id and rec.product_id.ipnr_has_amount:
                price = self.env["l10n.es.ipnr.amount"].get_ipnr_amount(
                    rec[rec._ipnr_secondary_unit_fields["parent_id"]][
                        rec._ipnr_secondary_unit_fields["date_field"]
                    ]
                )
                quantity = rec[
                    rec._ipnr_secondary_unit_fields["uom_field"]
                ]._compute_quantity(
                    rec[rec._ipnr_secondary_unit_fields["qty_field"]],
                    rec.product_id.uom_id,
                )
                weight = quantity * rec.product_id.plastic_weight_non_recyclable
                ipnr_amount = weight * price
            rec.ipnr_amount = ipnr_amount
