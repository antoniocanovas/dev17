from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    pnt_product_ids = fields.Many2many('product.product', store=False, string='Pricelist products',
                                   related='order_id.pricelist_id.pnt_product_ids')

    # Campos relativos al impuesto del plático:
    @api.depends('product_id', 'product_uom_qty')
    def _get_plastic_unit_tax(self):
        for record in self:
            total = 0
            if record.product_id and record.product_uom_qty:
                total = record.product_id.pnt_plastic_1000unit_tax * record.product_uom_qty / 1000
            record['pnt_plastic_tax'] = total
    pnt_plastic_tax = fields.Float('Plastic tax', store=True, compute='_get_plastic_unit_tax')

    @api.depends('product_id', 'product_uom_qty')
    def _get_plastic_kg(self):
        for record in self:
            total = 0
            if record.product_id and record.product_uom_qty:
                total = record.product_id.pnt_plastic_weight * record.product_uom_qty
            record['pnt_plastic_kg'] = total
    pnt_plastic_kg = fields.Float('Plastic Kg', store=True, compute='_get_plastic_kg')
