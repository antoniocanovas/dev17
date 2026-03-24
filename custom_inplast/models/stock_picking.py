from __future__ import annotations

from odoo import api, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.depends(
        "move_ids.weight",
        "move_ids.product_id.weight",
        "move_ids.product_uom_qty",
        "move_ids.product_uom",
    )
    def _cal_weight(self):
        for picking in self:
            picking.move_ids.filtered(lambda m: m.state != "cancel")._cal_move_weight()
        return super()._cal_weight()
