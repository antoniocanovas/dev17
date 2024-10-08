# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64
from datetime import datetime
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta

from odoo import fields, models, _, api
from odoo.exceptions import UserError
from odoo.tools import file_open


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.depends('bom_id')
    def _get_mrp_tool(self):
        for record in self:
            record['mrp_tool_id'] = record.bom_id.mrp_tool_id.id
    mrp_tool_id = fields.Many2one('mrp.product.tool', string='MRP Tool', store=True, readonly=False, compute='_get_mrp_tool')
    def add_pallet_boxes(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pallet.boxes.wizard',
            'views': [[self.env.ref('mrp_inplast.view_add_pallet_boxes_wizard').id, 'form']],
            'name': _('Add Boxes'),
            'target': 'new',
            'context': {
                'production_id': self.id,
            }
        }
        # Sobreescribe la función de mrp_lot_as_serial para tener en cuenta los lotes de cajas documentadas al fabricar palet:

    @api.constrains('lot_producing_id')
    def update_lot_as_serial(self):
        # Son stock.move, buscamos sólo los que son tipo packing = palet del campo raw_move_ids:
        sms = self.env['stock.move'].search(
            [('id', 'in', self.move_raw_ids.ids), ('product_id.pnt_product_type', '=', 'packing')])
        boxeslot = []
        for sm in sms:
            if sm.move_line_ids.lot_id.related_boxes_ids:
                for li in sm.move_line_ids.lot_id.related_boxes_ids:
                    boxeslot.append(li.id)

        if boxeslot == [] and len(self.move_raw_ids) > 1:
            super().update_lot_as_serial()
        elif len(boxeslot) > 0 and len(self.move_raw_ids) == 1 and self.move_raw_ids[0].picked:
            # Comprobar el número de lotes origen y destino, si no coinciden mensaje de error.
            # Asignar los lotes que ya existen a las cajas desmontadas.
            if len(boxeslot) != len(self.finished_move_line_ids):
                raise UserError(_("No coincide el número de cajas con los lotes disponibles!"))
            else:
                i = 0
                for li in self.finished_move_line_ids:
                    li.write({'lot_id': boxeslot[i]})
                    i += 1


