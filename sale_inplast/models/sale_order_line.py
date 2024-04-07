from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # Productos disponibles para este cliente, según su tarifa:
    pnt_product_ids = fields.Many2many('product.product', store=False, string='Pricelist products',
                                   related='order_id.pricelist_id.pnt_product_ids')


    # Campos para pasar de tapones a palets, en caso de vender por palets:
    pnt_base_unit = fields.Integer('Base qty')

    @api.onchange('pnt_base_unit')
    def _get_packing_units_from_base_qty(self):
        for li in self:
            qty = 0
            if (li.product_id.pnt_product_type == 'packing') and (li.product_id.pnt_parent_qty > 0):
                qty = li.pnt_base_unit / li.product_id.pnt_parent_qty
            li['pnt_base_uom_unit'] = qty
    pnt_base_uom_unit = fields.Float('Pack', store=False, compute='_get_packing_units_from_base_qty')

    @api.onchange('product_uom_qty')
    def _get_packing_units_from_sale_qty(self):
        for li in self:
            base_qty = 0
            if (li.product_id.pnt_product_type == 'packing'):
                base_qty = li.product_uom_qty * li.product_id.pnt_parent_qty
            li['pnt_base_sale_unit'] = base_qty
    pnt_base_sale_unit = fields.Integer('Base', store=False, compute='_get_packing_units_from_sale_qty')
