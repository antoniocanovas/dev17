# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    ipnr_has_amount = fields.Boolean(compute="_compute_ipnr_has_amount", store=True)

    @api.depends("ipnr_subject", "categ_id", "categ_id.ipnr_subject")
    def _compute_ipnr_has_amount(self):
        for rec in self:
            rec.ipnr_has_amount = rec.ipnr_subject == "yes" or (
                    rec.ipnr_subject == "category" and rec.categ_id.ipnr_subject
            )

    is_plastic_tax = fields.Boolean(string="Is plastic tax?", compute="_compute_is_plastic_tax", tracking=True)

    @api.depends("ipnr_subject", "categ_id", "categ_id.ipnr_subject")
    def _compute_is_plastic_tax(self):
        for rec in self:
            is_plastic_tax = False
            if rec.ipnr_subject == "yes" or (
                    rec.ipnr_subject == "category" and rec.categ_id.ipnr_subject):
                is_plastic_tax = True
            rec.is_plastic_tax = is_plastic_tax