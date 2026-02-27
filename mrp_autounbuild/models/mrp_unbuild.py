# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.exceptions import UserError


class MrpUnbuild(models.Model):
    _inherit = 'mrp.unbuild'

    @api.model
    def action_unbuild_from_barcode(self, lot_id):
        lot = self.env['stock.lot'].browse(lot_id)
        quant = self.env['stock.quant'].search([
            ('lot_id', '=', lot.id),
            ('quantity', '>', 0),
        ], limit=1)
        if not quant:
            raise UserError(_(
                'There is no stock available for lot %s.'
            ) % lot.name)

        bom_by_product = self.env['mrp.bom']._bom_find(
            lot.product_id, bom_type='normal'
        )
        bom = bom_by_product[lot.product_id]
        if not bom:
            raise UserError(
                _('This product does not have a bill of materials.')
            )

        unbuild_order = self.create({
            'product_id': lot.product_id.id,
            'bom_id': bom.id,
            'lot_id': lot.id,
            'location_id': quant.location_id.id,
            'location_dest_id': quant.location_id.id,
        })
        unbuild_order.action_unbuild()
        return unbuild_order.id
