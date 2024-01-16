from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    pnt_tracking_date = fields.Date('Tracking date', store=True, copy=False)
    pnt_new_price = fields.Float('New price', store=True, copy=False, digits=(3,6))
    pnt_product_state = fields.Boolean('Active', related='product_tmpl_id.active', store=False)

    # Al crear la línea asigna el precio del impuesto, aunque aún no se haya actualizado la tarifa nunca:
    @api.onchange('product_id','product_tmpl_id')
    def _update_plastic_tax(self):
        if self.pricelist_id.pnt_plastic_tax:
            self.price_surcharge = self.product_tmpl_id.pnt_plastic_1000unit_tax / 1000
