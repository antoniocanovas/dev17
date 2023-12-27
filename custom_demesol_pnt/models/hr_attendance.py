# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api
from datetime import timedelta


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    @api.depends('check_in','create_date')
    def auto_update_checkout(self):
        self.check_out = self.check_in + timedelta(hours=8)
    check_out = fields.Datetime(readonly=False, compute='auto_update_checkout')