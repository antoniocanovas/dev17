# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _inherit = "res.partner"

    expiration_task_ids = fields.One2many('project.task', 'partner_id', string='Expiration tasks')

    def _get_expiration_task_count(self):
        self.expiration_task_count = len(self.expiration_task_ids.ids)
    expiration_task_count = fields.Integer('Expiration count', compute='_get_expiration_task_count')