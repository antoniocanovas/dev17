# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


import logging

_logger = logging.getLogger(__name__)


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    pnt_raw_type = fields.Selection(
        [('weight','Weight'),('volume','Volume')],
        string='Distribution type',
        store=True,
        default='weight',
    )

    # Cantidad de producto (peso o volumen) a distribuir entre productos de esta categoría según product.template:
    @api.depends('product_tmpl_id', 'product_uom_id', 'product_tmpl_id.weight', 'product_tmpl_id.volume', 'product_qty', 'pnt_raw_type')
    def _get_product_raw_qty(self):
        for record in self:
            qty = 0
            factor = record.product_uom_id._compute_quantity(record.product_qty, record.product_tmpl_id.uom_id)
            if record.pnt_raw_type == 'weight':
                qty = record.product_tmpl_id.weight * factor * record.product_qty
            if record.pnt_raw_type == 'volume':
                qty = record.product_tmpl_id.volume * factor * record.product_qty
            record['pnt_raw_qty'] = qty
    pnt_raw_qty = fields.Float('UOM Qty', store=True, compute='_get_product_raw_qty')
