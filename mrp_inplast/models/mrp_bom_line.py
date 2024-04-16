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
            qty = record.product_qty
            if (record.pnt_raw_percent != 0) and (
                    record.pnt_raw_type_id == record.product_uom_category_id):
                qty = record.bom_id.pnt_raw_qty * record.pnt_raw_percent / 100

            record.product_qty = qty
