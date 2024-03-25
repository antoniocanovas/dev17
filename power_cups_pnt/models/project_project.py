from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class ProjectProject(models.Model):
    _inherit = 'project.project'

    pnt_power_cups_id = fields.Many2one('power.cups', string='CUPS', store=True, copy=False)
