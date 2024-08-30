# Copyright 2021 Pedro Guirao - Ingenieriacloud.com


from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    last_alternative_product_ids = fields.Many2many(comodel_name='product.template',
                                                   relation='product_tmpl_alternative_rel',
                                                   column1='product1_id',
                                                   column2='product2_id',
                                                   string='Last alternative products',
                                                   store="True")

    last_accessory_product_ids = fields.Many2many(comodel_name='product.product',
                                                  relation='product_product_accessory_rel',
                                                  column1='product1_id',
                                                  column2='product2_id',
                                                  string='Last accessory products',
                                                  store="True")
#                                                   relation='product_lead_rel',
