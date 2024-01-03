# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api, _
from odoo.exceptions import UserError

class ProjectProject(models.Model):
    _inherit = "project.project"

    pnt_sale_subtotal = fields.Monetary('Sale amount', store=True, related='sale_order_id.amount_untaxed')