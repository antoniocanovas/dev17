# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    ipnr_subject = fields.Selection(
        [("category", "Category"), ("yes", "Yes"), ("no", "No")],
        default="category",
        string="Subject To IPNR",
        required=True,
    )

    tax_plastic_type = fields.Selection(
        selection=[
            ("manufacturer", _("Manufacturer")),
            ("acquirer", _("Acquirer")),
            # ("both", _("Both")),
        ],
    )

    plastic_tax_weight = fields.Float(
        string="Plastic weight",
        digits="IPNR Weight",
    )
    plastic_weight_non_recyclable = fields.Float(
        string="Plastic weight non recyclable",
        digits="IPNR Weight",
    )

    @api.onchange("categ_id", "name", "ipnr_subject")
    def _onchange_categ_id_tax_plastic_type(self):
        """Set tax_plastic_type based on category configuration when
        category changes."""

        if self.ipnr_subject == "category":
            if (
                self.categ_id
                and self.categ_id.ipnr_subject
                and not self.tax_plastic_type
            ):
                self.tax_plastic_type = self.categ_id.tax_plastic_type
            elif self.categ_id and not self.categ_id.ipnr_subject:
                self.ipnr_subject = "no"

        # if self.categ_id and self.categ_id.tax_plastic_type:
        #     self.tax_plastic_type = self.categ_id.tax_plastic_type
        #     self.ipnr_subject = "yes"
        #
        # if not self.categ_id.ipnr_subject:
        #     self.ipnr_subject = "no"
