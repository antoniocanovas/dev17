# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # Campos para el impuesto al plástico:
    pnt_plastic_tax_weight = fields.Float('Plastic tax weight', store=True, related='categ_id.pnt_pricelist_weight')
    pnt_is_manufactured = fields.Boolean('Manufactured', store=True, related='categ_id.pnt_is_manufactured')

    def _get_plastic_unit_tax(self):
        self.pnt_plastic_unit_tax = self.env.company.pnt_plastic_tax * self.pnt_plastic_tax_weight
    pnt_plastic_unit_tax = fields.Monetary('Plastic tax', store=False, compute='_get_plastic_unit_tax', digits=(3,4))
