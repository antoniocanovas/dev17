# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_pallet2pack(self):
        pallet_types = self.env.company.pallet_packaging_ids
        if not pallet_types:
            return
        MoveLine = self.env['stock.move.line']
        for picking in self:
            for ml in list(picking.move_line_ids):
                packaging = ml.move_id.product_packaging_id
                if not packaging:
                    continue
                if packaging.package_type_id not in pallet_types:
                    continue
                if ml.result_package_id:
                    continue
                qty = int(ml.quantity)
                if qty <= 0:
                    continue
                lot_id = False
                lot_name = False
                if ml.product_id.tracking == 'lot':
                    lot_id = ml.lot_id.id
                    lot_name = ml.lot_name
                ml.quantity = 1
                ml.result_package_id = self.env['stock.quant.package'].create({
                    'package_type_id': packaging.package_type_id.id,
                })
                for _ in range(qty - 1):
                    new_package = self.env['stock.quant.package'].create({
                        'package_type_id': packaging.package_type_id.id,
                    })
                    MoveLine.create({
                        'move_id': ml.move_id.id,
                        'picking_id': picking.id,
                        'product_id': ml.product_id.id,
                        'product_uom_id': ml.product_uom_id.id,
                        'location_id': ml.location_id.id,
                        'location_dest_id': ml.location_dest_id.id,
                        'lot_id': lot_id,
                        'lot_name': lot_name,
                        'quantity': 1,
                        'result_package_id': new_package.id,
                    })
