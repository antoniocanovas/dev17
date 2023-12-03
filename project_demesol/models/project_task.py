from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class ProjectTask(models.Model):
    _inherit = 'project.task'


    state = fields.Selection(selection_add = [('1_waiting_customer', "Waiting customer"), ('03_approved',)],
                             ondelete={'05_waiting_customer': 'set default'}
    )


    # Nº de tareas no terminadas de las que depende, para usar en filtro:
    @api.depends('state','depend_on_ids.state', 'active', 'depend_on_ids.active')
    def _get_depend_count(self):
        for record in self:
            record['pnt_depend_count'] =  self.env['project.task'].search_count([
                ('id', 'in', record.depend_on_ids.ids),
                ('state', 'not in', ['1_done', '1_canceled']),
                ('active', '=', True)
            ])
    pnt_depend_count = fields.Integer('Dependencies count', store=True, compute='_get_depend_count', default=0)
