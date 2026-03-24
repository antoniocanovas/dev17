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

    def action_view_analytic_lines(self):
        """
        Esta acción corrige un typo en el módulo base 'analytic_distribution_base'.
        El error original era 'seclf' en lugar de 'self'.
        """
        action = self.env['ir.actions.act_window']._for_xml_id('account.action_account_analytic_line_list')
        ctx = dict(self.env.context)
        ctx.update({
            'search_default_analytic_distribution_template_id': self.template_id.id,
            'search_default_analytic_distribution_id': self.distribution_id.id,
        })
        action['context'] = ctx
        # El typo estaba aquí, en el dominio. Se ha corregido 'seclf' por 'self'.
        action['domain'] = [('id', 'in', self.analytic_line_ids.ids)]
        return action
