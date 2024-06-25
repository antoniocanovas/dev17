# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


import logging

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def get_split_mrp_as_serial(self):

        for li in self.finished_move_line_ids:
            qty = int(li.quantity - 1)
            li.write({'quantity': 1})
            for i in range(qty):
                self.env['stock.move.line'].create(
                    {'product_id': li.product_id.id, 'production_id': self.id,
                     'quantity': 1, 'state': 'confirmed', 'move_id': li.move_id.id})


    def action_confirm(self):
        res = super().action_confirm()
        if self.product_id.pnt_mrp_as_serial:
            self.create_lot_number()
            self.get_split_mrp_as_serial()
        return True

    def create_lot_number(self):
        if (self.product_id.tracking == 'lot') and (not self.lot_producing_id.id):
            name = self.name.split("/")[0] + self.name.split("/")[1] + self.name.split("/")[2]
            newlot = self.env['stock.lot'].create({'name': name, 'product_id': self.product_id.id})
            self.lot_producing_id = newlot.id


    def update_lot_as_serial(self):
        seq = self.lot_producing_id.pnt_mrp_serial
        mo_lot = self.lot_producing_id

        for li in self.finished_move_line_ids:
            name = mo_lot.name + "." + str(seq)
            lot = self.env['stock.lot'].search([('product_id', '=', li.product_id.id), ('name', '=', name)])
            if not lot.id:
                lot = self.env['stock.lot'].create({'product_id': li.product_id.id, 'name': name})
            li.write({'lot_id': lot.id})
            seq += 1

        mo_lot.write({'pnt_mrp_serial': seq})

    def update_unreserve_reserve_primary_lot(self):
        # Unreserve / Reserve, to pass original unique lot => New lots:
        pickings, productions = [], []
        mo_lot = self.lot_producing_id
        sml = self.env['stock.move.line'].search(
            [('product_id', '=', self.product_id.id), ('lot_id', '=', mo_lot.id),('picking_id','!=',False)])
        for li in sml:
            if li.picking_id not in pickings:
                pickings.append(li.picking_id)

        for pi in pickings:
            pi.do_unreserve()
            pi.action_assign()

    def button_mark_done(self):
        res = super().button_mark_done()
        if self.product_id.pnt_mrp_as_serial:
            self.update_lot_as_serial()
            self.update_unreserve_reserve_primary_lot()
        return res