# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api
from odoo.exceptions import UserError

class SignSendRequest(models.Transient):
    _inherit = "sign.send.request"

    task_id = fields.Many2one('project.task', string='Task')
