# Copyright 2024 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    ipnr_amount_subtotal = fields.Monetary(
        compute="_compute_ipnr_amount", compute_sudo=True
    )
    ipnr_amount_tax = fields.Monetary(
        compute="_compute_ipnr_amount", compute_sudo=True
    )
    ipnr_amount_total = fields.Monetary(
        compute="_compute_ipnr_amount", compute_sudo=True
    )
    picking_total_with_ipnr = fields.Monetary(
        compute="_compute_ipnr_amount", compute_sudo=True
    )

    @api.depends(
        "amount_total",
        "move_line_ids.ipnr_amount_subtotal",
        "move_line_ids.ipnr_amount_tax",
        "move_line_ids.ipnr_amount_total",
    )
    def _compute_ipnr_amount(self):
        for pick in self:
            ipnr_amount_subtotal = ipnr_amount_tax = ipnr_amount_total = 0.0
            for line in pick.move_line_ids:
                ipnr_amount_subtotal += line.ipnr_amount_subtotal
                ipnr_amount_tax += line.ipnr_amount_tax
                ipnr_amount_total += line.ipnr_amount_total
            pick.ipnr_amount_subtotal = ipnr_amount_subtotal
            pick.ipnr_amount_tax = ipnr_amount_tax
            pick.ipnr_amount_total = ipnr_amount_total
            pick.picking_total_with_ipnr = (
                pick.ipnr_amount_total + pick.amount_total
            )
