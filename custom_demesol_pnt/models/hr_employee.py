# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api
from datetime import timedelta


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    auto_checkout = fields.Boolean('Auto checkout', store=True, copy=True, default=True,
                                   help='Auto check out on daily attendances, if enabled')