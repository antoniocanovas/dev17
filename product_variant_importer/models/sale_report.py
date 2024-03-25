# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api


class SaleReport(models.Model):
    _inherit = "sale.report"


    @api.depends('product_id')
    def _get_product_color(self):
        self.color_attribute_id = self.product_id.color_attribute_id.id
    color_attribute_id = fields.Many2one('product.attribute.value', string='Color', store=True,
                                         compute='_get_product_color')

    @api.depends('product_id')
    def _get_product_size(self):
        self.size_attribute_id = self.product_id.size_attribute_id.id
    size_attribute_id = fields.Many2one('product.attribute.value', string='Size', store=True,
                                        compute='_get_product_size')

    @api.depends('product_id')
    def _get_product_shoes_model(self):
        self.product_tmpl_model_id = self.product_id.product_tmpl_model_id.id
    product_tmpl_model_id = fields.Many2one('product.template', string='Model', store=True,
                                            compute='_get_product_shoes_model')

    @api.depends('product_id')
    def _get_shoes_pair_count(self):
        for record in self:
            pairs_count = 1
            if record.product_id.pairs_count: pairs_count = record.product_id.pairs_count
            record['pairs_count'] = pairs_count * record.product_uom_qty
    pairs_count = fields.Integer('Pairs', store=True, compute='_get_shoes_pair_count')

    referrer_id = fields.Many2one('res.partner', string='Referrer')

    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res['color_attribute_id'] = "p.color_attribute_id"
        res['size_attribute_id'] = "p.size_attribute_id"
        res['product_tmpl_model_id'] = "t.product_tmpl_model_id"
        res['referrer_id'] = "s.referrer_id"
        res['pairs_count'] = "l.pairs_count"
        return res

    def _group_by_sale(self):
        res = super()._group_by_sale()
        res += """,
        p.color_attribute_id,
        p.size_attribute_id,
        t.product_tmpl_model_id,
        s.referrer_id,
             l.pairs_count"""
        return res