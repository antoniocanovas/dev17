# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


import logging

_logger = logging.getLogger(__name__)


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    pnt_raw_type_id = fields.Many2one('uom.category', string='Distribution type')

    # Método interno para ser llamado desde una BA, para los casos de Lista de Materiales por %
    def bom_percent_update(self):
        for record in self:
            if record.pnt_raw_type_id.id:
                uom_ref = self.env['uom.uom'].search([
                    ('category_id', '=', record.pnt_raw_type_id.id),
                    ('uom_type', '=', 'reference')])
                bom_qty = record.pnt_raw_qty
                for li in record.bom_line_ids:
                    if (li.pnt_raw_percent != 0) and (li.product_uom_category_id == li.pnt_raw_type_id):
                        factor = uom_ref._compute_quantity(bom_qty, li.product_id.uom_id)
                    li['product_qty'] = li.pnt_raw_percent / 100 * factor

    @api.depends('product_tmpl_id', 'pnt_raw_type_id')
    def _get_default_uom(self):
        uom = self.env['uom.uom'].search([
            ('category_id', '=', self.pnt_raw_type_id.id),
            ('uom_type', '=', 'reference')])
        self.pnt_raw_uom_id = uom.id
    pnt_raw_uom_id = fields.Many2one('uom.uom', string='UOM', store=True, compute='_get_default_uom')

    @api.depends('product_id')
    def _get_uom_available(self):
        weight = self.env.ref('uom.product_uom_categ_kgm')
        volume = self.env.ref('uom.product_uom_categ_vol')
        self.pnt_raw_available_ids = [(6,0,[weight.id, volume.id])]
    pnt_raw_available_ids = fields.Many2many('uom.category', string='Raw types available', compute='_get_uom_available')


    # Cantidad de producto (peso o volumen) a distribuir entre productos de esta categoría según product.template:
    @api.depends('product_tmpl_id', 'product_uom_id', 'product_tmpl_id.weight', 'product_tmpl_id.volume', 'product_qty', 'pnt_raw_type_id')
    def _get_product_raw_qty(self):
        for record in self:
            qty = 0
            # factor = unidad_origen(cantidad_origen, unidad_destino)
            factor = record.product_uom_id._compute_quantity(record.product_qty, record.product_tmpl_id.uom_id)
            if record.pnt_raw_type_id == self.env.ref('uom.product_uom_categ_kgm'):
                qty = record.product_tmpl_id.weight * factor
            if record.pnt_raw_type_id == self.env.ref('uom.product_uom_categ_vol'):
                qty = record.product_tmpl_id.volume * factor
            record['pnt_raw_qty'] = qty
    pnt_raw_qty = fields.Float('UOM Qty', store=True, compute='_get_product_raw_qty', digits='Stock Weight')
