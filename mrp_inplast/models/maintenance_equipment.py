# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api

import logging

_logger = logging.getLogger(__name__)


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    # Datos de empresa de categoría de moldes y accesorios para usar en dominios de equipos:
    pnt_mrp_tool_categ_id = fields.Many2one('maintenance.equipment.category', store=False,
                                            related='company_id.pnt_mrp_tool_categ_id')
    pnt_mrp_accesory_categ_id = fields.Many2one('maintenance.equipment.category', store=False,
                                                related='company_id.pnt_mrp_accesory_categ_id')

    pnt_tool_id = fields.Many2one('maintenance.equipment', string='Tool', store=True)
    pnt_accesory_ids = fields.One2many('maintenance.equipment', 'pnt_tool_id', string='Accesories', store=True)
    pnt_workcenter_ids = fields.Many2many('mrp.workcenter', store=True, copy=True, string='Other workcenters')