# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProjectMilestone(models.Model):
    _inherit = 'project.milestone'

    def _get_task_resume(self):
        for record in self:
            closed_tasks = 0
            closed = self.env['project.task'].search_count([
                ('state', 'in', ['1_done', '1_canceled']),
                ('id', 'in', record.task_ids.ids)])
            if closed.ids: closed_tasks = closed
            name = "(" + str(closed_tasks) + " / " + str(record.task_count) + ")"
            record['task_resume'] = name
    task_resume = fields.Char(string="Status", compute="_get_task_resume", store=False)
