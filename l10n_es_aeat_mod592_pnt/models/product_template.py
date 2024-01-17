# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # Campos para el impuesto al plástico:
    @api.onchange('categ_id')
    def _get_plastic_default_weight(self):
        self.pnt_plastic_weight = self.categ_id.pnt_pricelist_weight
    pnt_plastic_weight = fields.Float('Plastic tax weight', compute='_get_plastic_default_weight')

    pnt_is_manufactured = fields.Boolean('Manufacture', store=True, related='categ_id.pnt_is_manufactured')

    @api.onchange('categ_id','pnt_plastic_weight', 'pnt_is_manufactured')
    def _get_plastic_unit_tax(self):
        for record in self:
            tax = self.env.company.pnt_plastic_tax
            record['pnt_plastic_1000unit_tax'] = tax * record.pnt_plastic_weight * 1000
    pnt_plastic_1000unit_tax = fields.Float('Plastic tax x 1000', store=False,
                                            digits='Product Price',
                                            compute='_get_plastic_unit_tax')
