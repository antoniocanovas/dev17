# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_round


class MrpUnbuild(models.Model):
    _inherit = 'mrp.unbuild'

    def _prepare_move_line_vals(self, move, origin_move_line, taken_quantity):
        vals = super()._prepare_move_line_vals(move, origin_move_line, taken_quantity)
        # Fallback UoM when origin_move_line is empty (no MO case)
        if not vals.get('product_uom_id'):
            vals['product_uom_id'] = move.product_uom.id
        # If the component had no lot traceability when the MO was produced but
        # now does, origin_move_line.lot_id will be empty and _action_done()
        # would fail. Find or create a lot with the same name as the finished
        # product's lot, but linked to the component product.
        if not vals.get('lot_id') and move.product_id.tracking != 'none' and self.lot_id:
            component_lot = self.env['stock.lot'].search([
                ('name', '=', self.lot_id.name),
                ('product_id', '=', move.product_id.id),
                ('company_id', '=', self.company_id.id),
            ], limit=1)
            if not component_lot:
                component_lot = self.env['stock.lot'].create({
                    'name': self.lot_id.name,
                    'product_id': move.product_id.id,
                    'company_id': self.company_id.id,
                })
            vals['lot_id'] = component_lot.id
        return vals

    def action_unbuild(self):
        self.ensure_one()
        if self.mo_id:
            return super().action_unbuild()

        # --- No MO case ---
        # Replicate action_unbuild skipping the MO tracking requirement.
        # Lot assignment for tracked components is handled by _prepare_move_line_vals.
        self._check_company()
        if self.product_id.tracking != 'none' and not self.lot_id:
            raise UserError(_('You should provide a lot number for the final product.'))

        consume_moves = self._generate_consume_moves()
        consume_moves._action_confirm()
        produce_moves = self._generate_produce_moves()
        produce_moves._action_confirm()
        produce_moves.quantity = 0

        finished_moves = consume_moves.filtered(lambda m: m.product_id == self.product_id)
        consume_moves -= finished_moves

        for finished_move in finished_moves:
            if float_compare(
                finished_move.product_uom_qty,
                finished_move.quantity,
                precision_rounding=finished_move.product_uom.rounding,
            ) > 0:
                finished_move_line_vals = self._prepare_finished_move_line_vals(finished_move)
                self.env['stock.move.line'].create(finished_move_line_vals)

        empty_move_line = self.env['stock.move.line']
        for move in produce_moves | consume_moves:
            if move._need_precise_unbuild():
                # No origin move lines from MO; create one move line per move
                # using our _prepare_move_line_vals which assigns lots by name.
                move_line_vals = self._prepare_move_line_vals(move, empty_move_line, move.product_uom_qty)
                self.env['stock.move.line'].create(move_line_vals)
            else:
                move.quantity = float_round(
                    move.product_uom_qty,
                    precision_rounding=move.product_uom.rounding,
                )

        (finished_moves | consume_moves | produce_moves).picked = True
        finished_moves._action_done()
        consume_moves._action_done()
        produce_moves._action_done()
        produced_move_line_ids = produce_moves.mapped('move_line_ids').filtered(lambda ml: ml.quantity > 0)
        consume_moves.mapped('move_line_ids').write({'produce_line_ids': [(6, 0, produced_move_line_ids.ids)]})
        return self.write({'state': 'done'})

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

        # Find product and BOM even if there's no MO
        product = lot.product_id
        bom = self.env['mrp.bom']._bom_find(product, company_id=self.env.company.id, bom_type='normal')[product]

        unbuild_vals = {
            'product_id': product.id,
            'bom_id': bom.id if bom else False,
            'product_uom_id': product.uom_id.id,
            'lot_id': lot.id,
            'product_qty': 1.0,
            'location_id': quant.location_id.id,
            'location_dest_id': quant.location_id.id,
        }
        if production:
            unbuild_vals['mo_id'] = production.id

        unbuild_order = self.create(unbuild_vals)
        unbuild_order.action_unbuild()
        return unbuild_order.id
