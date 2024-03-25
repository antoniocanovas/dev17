# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError

class AccountMove(models.Model):
    _inherit = "account.move"

    # Comercialmente en cada pedido quieren saber cuántos pares se han facturado:
    def _get_shoes_pair_count(self):
        for record in self:
            count = 0
            for li in record.invoice_line_ids:
                count += li.pairs_count
            record['pairs_count'] = count
    pairs_count = fields.Integer('Pairs', store=False, compute='_get_shoes_pair_count')
