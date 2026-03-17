# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class StockUnbuildWizard(models.TransientModel):
    _name = 'stock.unbuild.wizard'
    _description = 'Stock Unbuild Wizard'

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        readonly=True,
    )
    lot_id = fields.Many2one(
        'stock.lot',
        string='Lot/Serial Number',
        required=True,
        domain="[('product_id', '=', product_id), ('product_qty', '>', 0)]",
    )
    location_id = fields.Many2one(
        'stock.location',
        string='Location',
        required=True,
    )
    bom_id = fields.Many2one(
        'mrp.bom',
        string='Bill of Materials',
        compute='_compute_bom_id',
        readonly=True,
    )
    mo_id = fields.Many2one(
        'mrp.production',
        string='Manufacturing Order',
    )

    @api.depends('product_id')
    def _compute_bom_id(self):
        for wizard in self:
            bom = self.env['mrp.bom'].search([
                '|',
                ('product_id', '=', wizard.product_id.id),
                '&',
                ('product_tmpl_id', '=', wizard.product_id.product_tmpl_id.id),
                ('product_id', '=', False),
                ('type', '=', 'normal'),
                ('company_id', 'in', [self.env.company.id, False]),
            ], limit=1)
            if not bom:
                raise UserError(
                    _('This product does not have a bill of materials.')
                )
            wizard.bom_id = bom.id

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        if self.lot_id:
            # Set location from quant
            stock_quant = self.env['stock.quant'].search([
                ('lot_id', '=', self.lot_id.id),
                ('quantity', '>', 0),
            ], limit=1)
            if stock_quant:
                self.location_id = stock_quant.location_id.id

            # --- Robust MO search ---
            production = self.env['mrp.production']
            # 1. Try the most direct link first
            production = self.env['mrp.production'].search([
                ('lot_producing_id', '=', self.lot_id.id),
                ('state', '=', 'done'),
            ], limit=1)

            # 2. If that fails, search through stock moves as a fallback
            if not production:
                move_line = self.env['stock.move.line'].search([
                    ('lot_id', '=', self.lot_id.id),
                    ('state', '=', 'done'),
                    ('production_id', '!=', False),
                    ('quantity', '>', 0),
                ], limit=1, order='date desc')
                if move_line:
                    production = move_line.production_id
            
            self.mo_id = production.id if production else False

    def action_confirm(self):
        self.ensure_one()
        unbuild_vals = {
            'product_id': self.product_id.id,
            'bom_id': self.bom_id.id if self.bom_id else False,
            'product_uom_id': self.mo_id.product_uom_id.id if self.mo_id else self.product_id.uom_id.id,
            'lot_id': self.lot_id.id,
            'product_qty': 1.0,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_id.id,
        }
        if self.mo_id:
            unbuild_vals['mo_id'] = self.mo_id.id

        unbuild_order = self.env['mrp.unbuild'].create(unbuild_vals)

        unbuild_order.action_unbuild()
        return {'type': 'ir.actions.act_window_close'}
