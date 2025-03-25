from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # Productos disponibles para este cliente, según su tarifa:
    pnt_product_ids = fields.Many2many('product.product', store=False, string='Pricelist products',
                                   related='order_id.pricelist_id.pnt_product_ids')

    pnt_product_type = fields.Selection(related="product_id.pnt_product_type")

    @api.onchange('product_uom_qty','product_id','product_packaging_id','product_packaging_qty')
    def _get_base_units(self):
        for li in self:
            qty = 0
            if (li.product_id.pnt_product_type == 'packing') and (li.product_id.pnt_parent_qty > 0):
                qty = li.product_uom_qty * li.product_id.pnt_parent_qty
            if (li.product_id.pnt_product_type == 'final'):
                qty = li.product_uom_qty
            li['pnt_base_qty'] = qty
    pnt_base_qty = fields.Integer('Base qty', store=False, compute='_get_base_units')


    @api.onchange('product_uom_qty')
    def _get_packing_units_from_sale_qty(self):
        for li in self:
            base_qty = 0
            if (li.product_id.pnt_product_type == 'packing'):
                base_qty = li.product_uom_qty * li.product_id.pnt_parent_qty
            li['pnt_base_sale_unit'] = base_qty
    pnt_base_sale_unit = fields.Integer('Base', store=False, compute='_get_packing_units_from_sale_qty')

    @api.onchange('list_price','discount')
    def _get_1k_price(self):
        for record in self:
            price = record.price_unit * 1000
            if record.pnt_base_qty != 0:
                price = record.price_subtotal / record.pnt_base_qty * 1000
            record['pnt_base_1k_price'] =  price
    pnt_base_1k_price = fields.Float('1K', compute='_get_1k_price')

    # Fecha manual para que el comercial indique la comprometida de llegada a casa del cliente:
    customer_arrival_date = fields.Date('Customer date', help='Customer committed date')

    # Campo para referencia antigua mientras se mantiene el sistema de producción anterior a Odoo, borrar después:
    old_default_code = fields.Char('Ref antigua')