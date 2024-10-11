# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api
from odoo.exceptions import UserError

class SignRequest(models.Model):
    _inherit = "sign.request"

    task_id = fields.Many2one('project.task', string='Task')
