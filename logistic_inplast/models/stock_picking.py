from odoo import _, api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    container_id = fields.Many2one('container.type', related='sale_id.container_id')