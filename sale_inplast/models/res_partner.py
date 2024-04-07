from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    property_product_pricelist = fields.Many2one('product.pricelist', store=True, index=True)
    pnt_pricelist_state = fields.Selection(related='property_product_pricelist.pnt_state', store=True)
    pnt_next_update = fields.Date(related='property_product_pricelist.pnt_next_update')

    # No funciona:
    def create_private_pricelist(self):
        my_pricelist = self.env['product.pricelist'].create({'name': self.name})
        self.write({'pricelist_id': my_pricelist.id})
