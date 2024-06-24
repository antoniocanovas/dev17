from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class ProductCategory(models.Model):
    _inherit = 'product.category'

#    pnt_pricelist_weight = fields.Float('Pricelist weight', store=True, copy=True)

    # Tipo de productos en subfamilia:
    pnt_product_type = fields.Selection([('final','End-product'),
                                         ('semi', 'Semi-finished'),
                                         ('packing','Packing'),
                                         ('raw', 'Raw'),
                                         ('dye', 'Dye'),
                                         ('packaging', 'Packaging'),
                                         ('other', 'Other')],
                                        store=True, copy=True, string='Product type')
