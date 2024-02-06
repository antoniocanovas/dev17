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

    @api.onchange('write_date')
    def _get_units_from_total_percent(self):
        for record in self:
            # Falta el if de que sea la misma clase de unidad y asginar la misma que del peso o volumen:
            if record.pnt_raw_percent != 0:
                qty = record.bom_id.pnt_raw_qty * record.pnt_raw_percent / 100
                uom = record.bom_id.product_tmpl_id.uom_id
                record.write({'product_qty': qty, 'product_uom_id': uom.id})