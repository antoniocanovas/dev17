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
    pnt_mrp_blade_categ_id = fields.Many2one('maintenance.equipment.category', store=False,
                                                related='company_id.pnt_mrp_blade_categ_id')

    pnt_tool_id = fields.Many2one('maintenance.equipment', string='Tool', store=True)
    #Campos para relacionar moldes con accesorios y viceversa
    pnt_accesory_tool_ids = fields.Many2many(comodel_name='maintenance.equipment',
                                             relation="mrp_mold_accesory_rel",
                                             column1="accesory_id",
                                             column2='tool_id',
                                             string='A.tools', store=True,
                                             help="Campo de Moldes para un Accesorio")

    pnt_tool_accesory_ids = fields.Many2many(comodel_name='maintenance.equipment',
                                        relation="mrp_mold_accesory_rel",
                                        column1='tool_id',
                                        column2="accesory_id",
                                        string='Accesories', store=True,
                                        help="Campo de Accesorios para un Molde")

    #Campos para relacionar moldes con cuchillas.
    pnt_blade_tool_ids = fields.Many2many(comodel_name='maintenance.equipment',
                                    relation="mrp_mold_blade_rel",
                                    column1="blade_id",
                                    column2='tool_id',
                                    string='B.tools', store=True,
                                    help="Campo de Moldes para una cuchilla")
    pnt_tool_blade_ids = fields.Many2many(comodel_name='maintenance.equipment',
                                        relation="mrp_mold_blade_rel",
                                        column1='tool_id',
                                        column2="blade_id",
                                        string='Blades', store=True,
                                        help="Campo de cuchillas para un Molde",)

    pnt_workcenter_ids = fields.Many2many('mrp.workcenter', store=True, copy=True, string='Other workcenters')

    estimated_rpm = fields.Integer("Estimated RPM")
    hole_count = fields.Integer("Hole Count")
