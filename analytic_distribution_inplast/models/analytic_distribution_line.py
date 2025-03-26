# -*- coding: utf-8 -*-
# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from docutils.nodes import container
from odoo import fields, models, api
from odoo.exceptions import UserError

class AnalyticDistributionLine(models.Model):
    _inherit = 'analytic.distribution.line'


    # =========================================================================
    # 12) Almacén
    # =========================================================================
    picking_hour_cost = fields.Float(string='Picking hour cost', compute='_compute_picking_hour_cost')

    def _compute_picking_hour_cost(self):
        for record in self:
            total = 0
            if record.distribution_id.picking_hour_qty > 0:
                total = record.balance / record.distribution_id.picking_hour_qty
            record.picking_hour_cost = -total
