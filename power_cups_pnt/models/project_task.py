from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class ProjectProject(models.Model):
    _inherit = 'project.task'

    pnt_power_cups_id = fields.Many2one('power.cups', string='CUPS', store=True, related='project_id.pnt_power_cups_id')
