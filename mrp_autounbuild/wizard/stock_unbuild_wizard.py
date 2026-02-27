# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


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
            stock_quant = self.env['stock.quant'].search([
                ('lot_id', '=', self.lot_id.id),
                ('quantity', '>', 0),
            ], limit=1)
            if stock_quant:
                self.location_id = stock_quant.location_id.id

    def action_confirm(self):
        self.ensure_one()
        quant = self.env['stock.quant'].search([
            ('lot_id', '=', self.lot_id.id),
            ('location_id', '=', self.location_id.id),
            ('quantity', '>', 0),
        ], limit=1)
        if not quant:
            raise UserError(_(
                'There is no stock available for lot %s in location %s.'
            ) % (self.lot_id.name, self.location_id.display_name))

        unbuild_order = self.env['mrp.unbuild'].create({
            'product_id': self.product_id.id,
            'bom_id': self.bom_id.id,
            'lot_id': self.lot_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_id.id,
        })
        try:
            unbuild_order.action_unbuild()
        except UserError as e:
            raise UserError(_(
                'An error occurred during the unbuild process: %s'
            ) % e.name)
        return {'type': 'ir.actions.act_window_close'}
