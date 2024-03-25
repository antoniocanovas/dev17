# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"


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

    @api.model
    def _select(self):
        select_str = super()._select()
        select_str += """
             , template.product_tmpl_model_id as product_tmpl_model_id
             , line.pairs_count
             , line.color_attribute_id as color_attribute_id
             , line.size_attribute_id as size_attribute_id
             """
        return select_str

    @api.model
    def _group_by(self):
        group_by_str = super()._group_by()
        group_by_str += ", template.product_tmpl_model_id, line.pairs_count, line.color_attribute_id"
        return group_by_str

#    def _select_additional_fields(self):
    #        res = super()._select_additional_fields()
    #    res['color_attribute_id'] = "p.color_attribute_id"
    #    res['size_attribute_id'] = "p.size_attribute_id"
    #    res['product_tmpl_model_id'] = "t.product_tmpl_model_id"
    #       res['pairs_count'] = "l.pairs_count"


#    return res

    #    def _group_by_sale(self):
    #    res = super()._group_by_sale()
    #    res += """,
    #    p.color_attribute_id,
    #    p.size_attribute_id,
    #    t.product_tmpl_model_id,
    #         l.pairs_count"""
#    return res