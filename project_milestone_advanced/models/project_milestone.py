# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProjectMilestone(models.Model):
    _inherit = 'project.milestone'

    @api.depends('state')
    def _get_task_resume(self):
        for record in self:
            closed = self.env['project.task'].search_count(
                [('state', 'in', ['1_done', '1_canceled']), ('id', 'in', record.task_ids.ids)])
            name = "(" + str(closed) + " / " + str(record.task_count) + ")"
            record['task_resume'] = name
    task_resume = fields.Char(store=False, copy=False, string="Status", compute="_get_task_resume")
