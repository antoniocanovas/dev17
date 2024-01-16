from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'


    # Campos para el recálculo automático o requerido de tarifas (error search, que busque en tarifa 01/2024):
#    pnt_pricelist_type = fields.Selection(store=True, string='Pricelist type',
#                                          related='property_product_pricelist.pnt_pricelist_type')
#    pnt_next_update = fields.Date('Pricelist next update', store=True,
#                                  related='property_product_pricelist.pnt_next_update')
