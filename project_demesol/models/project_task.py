from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class ProjectTask(models.Model):
    _inherit = 'project.task'

    pnt_cloudfolder = fields.Char('Cloud folder', store=False, related='project_id.pnt_cloudfolder')

    # Nº de tareas no terminadas de las que depende, para usar en filtro:
    @api.depends('state','depend_on_ids.state', 'active', 'depend_on_ids.active')
    def _get_in_progress_count(self):
        for record in self:
            record['pnt_in_progress_count'] =  self.env['project.task'].search_count([
                ('id', 'in', record.depend_on_ids.ids),
                ('state', 'not in', ['1_done', '1_canceled']),
                ('active', '=', True)
            ])
    pnt_in_progress_count = fields.Integer('Dependencies count', store=True, compute='_get_in_progress_count', default=0)

# Esto amplía la lista de opciones del estado en kanban, pero no sé aún cómo hacer que aparezca:
#    state = fields.Selection(selection_add = [('1_waiting_customer', "Waiting customer"), ('03_approved',)],
#                             ondelete={'1_waiting_customer': 'set default'}
#    )

