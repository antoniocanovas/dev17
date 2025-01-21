# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, _


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
            #("both", _("Both")),
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