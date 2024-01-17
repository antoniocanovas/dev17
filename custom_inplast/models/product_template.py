# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"


    pnt_product_type = fields.Selection(string='Product type', related='categ_id.pnt_product_type')
    pnt_product_dye_id = fields.Many2one('product.template', string='Product dye', store=True, copy=True)

    pnt_product_coa = fields.Many2one(
        "pnt.coa",
        string="COA",
    )

    @api.depends('name', 'default_code', 'pnt_product_dye_id')
    def _compute_display_name(self):
        for template in self:
            template.display_name = '{}{}{}'.format(
                template.default_code and '[%s] ' % template.default_code or '',
                template.name, template.pnt_product_dye_id.name and ' [%s]' % template.pnt_product_dye_id.name or '')

