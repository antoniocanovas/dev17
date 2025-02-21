# -*- coding: utf-8 -*-
# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from docutils.nodes import container
from odoo import fields, models, api
from odoo.exceptions import UserError

class AnalyticDistributionLine(models.Model):
    _inherit = 'analytic.distribution.line'



    # =========================================================================
    # 12) Consolidados almacen
    # =========================================================================
    picking_hour_qty = fields.Float(string='Pickig hours',compute='_compute_picking_hour_qty')
    picking_hour_cost = fields.Float(string='Picking hour cost', compute='_compute_picking_hour_cost')

    @api.depends('date_from', 'date_to')
    def _compute_picking_hour_qty(self):
        for rec in self:
            parameters = self.env.ref('analytic_distribution_inplast.analytic_distribution_inplast_parameter')
            distribution = rec.distribution_id
            cistern_unload = parameters.raw_cistern_unload * distribution.picking_in_cistern_qty
            sack_unload = parameters.raw_sack_unload * distribution.picking_in_sack_qty
            color_unload = parameters.raw_color_unload * distribution.picking_in_color_qty
            cardboard_unload = parameters.raw_cardboard_unload * distribution.picking_in_cardboard_qty
            bag_unload = parameters.raw_bag_unload * distribution.picking_in_bag_qty
            pallet_unload = parameters.raw_pallet_unload * distribution.picking_in_pallet_qty
            internal_pickings = distribution.days * (parameters.raw_color_reloc_daily + parameters.raw_cboard_reloc_daily + parameters.raw_bag_reloc_daily + parameters.raw_pallet_reloc_daily)
            container_load = distribution.sale_container_qty * parameters.container_load

            rec.picking_hour_qty = cistern_unload + sack_unload + color_unload + cardboard_unload + bag_unload + pallet_unload + internal_pickings + container_load

    def _compute_picking_hour_cost(self):
        for record in self:
            total = 0
            if record.picking_hour_qty > 0:
                total = record.balance / record.picking_hour_qty
            record.picking_hour_cost = -total
