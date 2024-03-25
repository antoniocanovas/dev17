# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    # Comercialmente en cada pedido quieren saber cuántos pares se han vendido:
    @api.depends('product_id', 'product_uom_qty')
    def _get_shoes_sale_line_pair_count(self):
        for record in self:
            record['pairs_count'] = record.product_id.pairs_count * record.product_uom_qty
    pairs_count = fields.Integer('Pairs', store=True, compute='_get_shoes_sale_line_pair_count')

    shoes_campaign_id = fields.Many2one('project.project', string='Campaign', related='order_id.shoes_campaign_id')

    # Para informes:
    product_tmpl_model_id = fields.Many2one('product.template', string='Model', store=True,
                                            related='product_id.product_tmpl_model_id')
    color_attribute_id = fields.Many2one('product.attribute.value', string='Color', store=True,
                                            related='product_id.color_attribute_id')
    shoes_campaign_id = fields.Many2one('project.project', string='Campaign', store=True,
                                        related='order_id.shoes_campaign_id')
    product_brand_id = fields.Many2one('product.brand', string='Brand', store=True,
                                       related='product_id.product_brand_id')
    @api.depends('state')
    def _get_quoted_quantity(self):
        for record in self:
            total = 0
            if record.state not in ['sale','done','cancel']:
                total = record.product_uom_qty
            record['qty_quoted'] = total
    qty_quoted = fields.Float('Quoted qty', store=True, copy=False, compute='_get_quoted_quantity')

    # ========= FIN INFORMES


    # Precio por par según tarifa:
    @api.depends('product_id','price_unit')
    def _get_shoes_pair_price(self):
        for record in self:
            total = 0
            if record.pairs_count != 0: total = record.price_subtotal / record.pairs_count
            record['pair_price'] = total
    pair_price = fields.Float('Pair price', store=True, compute='_get_shoes_pair_price')

    product_saleko_id = fields.Many2one('product.product', string='Product KO', store=True, copy=True)

    @api.onchange('product_saleko_id')
    def change_saleproductok_2_saleproductko(self):
        self.product_id = self.product_saleko_id.id