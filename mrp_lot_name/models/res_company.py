# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api


class ResCompany(models.Model):
    _inherit = "res.company"

    pnt_mrp_lot_name = fields.Selection([('mo','Manufacturing order')], string='MRP lot name')