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

    @api.onchange('pnt_raw_percent','product_id')
    def _get_units_from_total_percent(self):
        qty = self._origin.product_qty
        if (self.pnt_raw_percent != 0) and (self.pnt_raw_type_id == self.product_uom_category_id):
            qty = self.bom_id.pnt_raw_qty * self.pnt_raw_percent / 100
        self.product_qty = qty
    product_qty = fields.Float(compute='_get_units_from_total_percent')

    @api.onchange('pnt_raw_percent','product_id')
    def _get_uom_from_percent_type(self):
        # Falta el if de que sea la misma clase de unidad y asginar la misma que del peso o volumen:
        uom = self._origin.product_uom_id
        if (self.pnt_raw_percent != 0) and (self.pnt_raw_type_id == self.product_uom_category_id):
            uom = self.env['uom.uom'].search([
                ('category_id','=',self.product_uom_category_id.id),
                ('uom_type','=','reference')
            ])
        self.product_uom_id = uom.id
    product_uom_id = fields.Many2one(compute='_get_uom_from_percent_type')