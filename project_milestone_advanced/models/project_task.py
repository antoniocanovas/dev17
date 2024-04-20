# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProjectTask(models.Model):
    _inherit = 'project.task'

    @api.depends('state')
    def _get_is_pending(self):
        for record in self:
            solution = 1
            if self.state in ['1_done', '1_canceled']: solution = 0
            record['pending'] = solution
    pending = fields.Integer(store=True, copy=False, string="Pending", readonly=True, compute="_get_is_pending")
