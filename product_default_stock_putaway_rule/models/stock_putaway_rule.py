# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api


class StockPutawayRule(models.Model):
    _inherit = "stock.putaway.rule"

    name = fields.Char('Name', compute='_get_name')
    def _get_name(self):
        name = ""
        if self.product_id.id and self.location_in_id.id and self.location_out_id.id:
            name = self.product_id.name + " From: " + self.location_in_id.name + " to: " + self.location_out_id.name
        self.name = name