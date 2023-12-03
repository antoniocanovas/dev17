from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class ProjectTask(models.Model):
    _inherit = 'project.task'

    # Nº de tareas no terminadas de las que depende, para usar en filtro:
    @api.depends('state','depend_on_ids.state', 'active', 'depend_on_ids.active')
    def _get_depend_count(self):
        for record in self:
            total = 0
            depends = self.env['project.task'].search([
                ('id', 'in', record.depend_on_ids.ids),
                ('state', 'not in', ['1_done', '1_canceled']),
                ('active', '=', True)
            ])
            if depends.ids: total = len(depends.ids)
            record['pnt_depend_count'] = total
    pnt_depend_count = fields.Integer('Dependencies count', store=True, compute='_get_depend_count')
