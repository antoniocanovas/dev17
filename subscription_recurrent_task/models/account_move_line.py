from odoo import _, api, fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    task_id = fields.Many2one('project.task', string='Task',store=True, copy=False)
    task_stage_id = fields.Many2one('project.task.type', string='Task stage', related='task_id.stage_id', store=False)
