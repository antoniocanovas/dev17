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

    @api.onchange('pnt_raw_percent')
    def _get_units_from_total_percent(self):
        # Falta el if de que sea la misma clase de unidad y asginar la misma que del peso o volumen:
        qty = self._origin.product_qty
        if self.pnt_raw_percent != 0:
            qty = self.bom_id.pnt_raw_qty * self.pnt_raw_percent / 100
#            uom = self.bom_id.product_tmpl_id.uom_id
        self.product_qty = qty
    product_qty = fields.Float(compute='_get_units_from_total_percent')