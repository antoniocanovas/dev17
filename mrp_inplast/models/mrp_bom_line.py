# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


import logging

_logger = logging.getLogger(__name__)


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    pnt_raw_percent = fields.Float('Percent')
    pnt_raw_type_id = fields.Many2one(related='bom_id.pnt_raw_type_id')
    product_qty = fields.Float(digits='Stock Weight', compute="_get_product_qty", store=True)
    bom_product_qty = fields.Float(related='bom_id.product_qty')

    @api.onchange('pnt_raw_percent','bom_product_qty')
    def _get_product_qty(self):
        for record in self:
            # unidad patron = "Reference" de la unidad de medida, es la que se usa en "Weight" del producto.
            # factor = unidad_origen._compute_quantity(cantidad_origen, unidad_destino)
            qty = record.product_qty
            if (record.pnt_raw_percent != 0) and (record.pnt_raw_type_id == record.product_uom_category_id):
                uom_ref = self.env['uom.uom'].search([
                    ('category_id', '=', record.pnt_raw_type_id.id),
                    ('uom_type', '=', 'reference')])
                factor = uom_ref._compute_quantity(record.bom_id.pnt_raw_qty, record.product_id.uom_id)
                qty = factor * record.pnt_raw_percent / 100

            record.product_qty = qty
