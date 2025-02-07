from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    pnt_tracking_date = fields.Date('Tracking date', store=True, copy=False)
    pnt_new_price = fields.Float('New price', store=True, copy=False, digits=(3,6))
    pnt_product_state = fields.Boolean('Active', related='product_tmpl_id.active', store=False)

    # Campos para poner como sólo lectura los precios de productos "packing" en vistas y recalcular precios:
    pnt_product_type = fields.Selection(related='product_tmpl_id.pnt_product_type')
    pnt_parent_id = fields.Many2one('product.template', related='product_tmpl_id.pnt_parent_id')

    def update_packing_products_price(self):
        for record in self:
            if record.pnt_product_type == 'final':
                packing_lines = self.env['product.pricelist.item'].search([
                    ('pricelist_id','=',record.pricelist_id.id),
                    ('pnt_parent_id','=',record.product_tmpl_id.id),
                ])
                for li in packing_lines:
                    li['fixed_price'] = record.fixed_price * li.product_tmpl_id.pnt_parent_qty
