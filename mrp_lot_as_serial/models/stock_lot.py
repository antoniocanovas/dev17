# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api


class StockLot(models.Model):
    _inherit = "stock.lot"

    pnt_mrp_serial = fields.Integer('MRP serial', store=True, default=1)
    parent_id = fields.Many2one("stock.lot", "Parent Lot")