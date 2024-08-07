# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api


class StockLot(models.Model):
    _inherit = "stock.move.line"

    serial_lot_id = fields.Many2one('stock.lot', string='Serial Lot',
                                 help='Internal field to rewrite in partial productions after confirm')