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

        # --- Robust MO search ---
        production = self.env['mrp.production']
        # 1. Try the most direct link first
        production = self.env['mrp.production'].search([
            ('lot_producing_id', '=', lot.id),
            ('state', '=', 'done'),
        ], limit=1)

        # 2. If that fails, search through stock moves as a fallback
        if not production:
            move_line = self.env['stock.move.line'].search([
                ('lot_id', '=', lot.id),
                ('state', '=', 'done'),
                ('production_id', '!=', False),
                ('quantity', '>', 0),
            ], limit=1, order='date desc')
            if move_line:
                production = move_line.production_id
        
        if not production:
            raise UserError(_(
                'Could not find the original Manufacturing Order for Lot %s.'
            ) % lot.name)

        # Create the unbuild order with all required fields explicitly.
        # NOTE: onchange methods don't run server-side, so product_id and
        # other fields that _onchange_mo_id would set must be provided here.
        unbuild_order = self.create({
            'mo_id': production.id,
            'product_id': production.product_id.id,
            'bom_id': production.bom_id.id if production.bom_id else False,
            'product_uom_id': production.product_uom_id.id,
            'lot_id': lot.id,
            'product_qty': 1.0,
            'location_id': quant.location_id.id,
            'location_dest_id': quant.location_id.id,
        })

        unbuild_order.action_unbuild()
        return unbuild_order.id
