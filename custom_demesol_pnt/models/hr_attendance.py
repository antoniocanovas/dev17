# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api
from datetime import timedelta


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    @api.depends('create_date')
    def auto_update_checkout(self):
        if self.employee_id.auto_checkout == True:
            self.check_out = self.check_in + timedelta(hours=8)
