# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    ipnr_subject = fields.Boolean(string="Subject to IPNR")
