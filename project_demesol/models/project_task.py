from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class ProjectTask(models.Model):
    _inherit = 'project.task'

    # Nº de tareas no terminadas de las que depende, para usar en filtro:
    @api.depends('state','depend_on_ids.state', 'active', 'depend_on_ids.active')
    def _get_depend_count(self):
         self.pnt_depend_count =  self.env['project.task'].search_count([
                ('id', 'in', record.depend_on_ids.ids),
                ('state', 'not in', ['1_done', '1_canceled']),
                ('active', '=', True)
            ])
    pnt_depend_count = fields.Integer('Dependencies count', store=True, compute='_get_depend_count')
