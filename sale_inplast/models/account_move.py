from odoo import _, api, fields, models
from odoo.exceptions import UserError
from datetime import datetime

import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends("state", "invoice_line_ids", "pricelist_id.pnt_state")
    def _get_invoice_pricelist_state(self):
        for record in self:
            state = False
            if (record.move_type in ["out_invoice"]) and (record.state == "draft"):
                state = record.pricelist_id.pnt_state
                if record.state in ["draft", "sent"]:
                    state = record.pricelist_id.pnt_state
            record["pnt_pricelist_state"] = state

    pnt_pricelist_state = fields.Selection(
        [("active", "Active"), ("update", "Update"), ("locked", "Locked")],
        string="Pricelist state",
        store=True,
        copy=False,
        compute="_get_invoice_pricelist_state",
    )

    pnt_last_price_update = fields.Datetime(
        "Last price update", default=lambda self: datetime.now()
    )

    def action_post(self):
        for line in self.invoice_line_ids:
            has_pricelist = self.env["product.pricelist.item"].search(
                [
                    ("pricelist_id", "=", self.pricelist_id.id),
                    ("product_tmpl_id", "=", line.product_id.product_tmpl_id.id),
                ]
            )
            if len(has_pricelist) > 1:
                raise UserError("El producto tiene más de un precio en la lista de precios:" + line.product_tmpl_id.name)
            if has_pricelist and (has_pricelist.fixed_price != line.price_unit):
                line._compute_price_unit()
        # result = super(AccountMove, self).button_update_prices_from_pricelist()
        result = super(AccountMove, self).action_post()
        self.pnt_last_price_update = datetime.now()

    def button_update_prices_from_pricelist(self):
        result = super(AccountMove, self).button_update_prices_from_pricelist()
        self.pnt_last_price_update = datetime.now()

    @api.depends("invoice_line_ids", "state")
    def _get_invoice_update_prices_required(self):
        for record in self:
            required = False
            last_update = record.pricelist_id.pnt_last_update
            if (
                (record.state in ["draft"])
                and (last_update)
                and (record.pnt_last_price_update < last_update)
            ):
                required = True
            record["pnt_update_prices"] = required

    pnt_update_prices = fields.Boolean(
        "Update prices", store=False, compute="_get_invoice_update_prices_required"
    )
