# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    ipnr_subject = fields.Boolean(string="Subject to IPNR")
    tax_plastic_type = fields.Selection(
        selection=[
            ("manufacturer", _("Manufacturer")),
            ("acquirer", _("Acquirer")),
        ],
        string="Default Plastic Type",
        help="Default plastic type that will be assigned to products in this category",
    )
