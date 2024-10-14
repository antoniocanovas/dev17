# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api

class SignSendRequest(models.AbstractModel):
    _inherit = "sign.send.request"

    task_id = fields.Many2one('project.task', string='Task')
