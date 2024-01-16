from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    pnt_product_ids = fields.Many2many('product.product', store=False, string='Pricelist products',
                                   related='move_id.pricelist_id.pnt_product_ids')

    # Campos relativos al impuesto del plático:
    @api.depends('product_id', 'quantity')
    def _get_plastic_unit_tax(self):
        for record in self:
            total = 0
            if record.product_id and record.quantity:
                total = record.product_id.pnt_plastic_1000unit_tax * record.quantity / 1000
            record['pnt_plastic_tax'] = total
    pnt_plastic_tax = fields.Float('Plastic tax', store=True, compute='_get_plastic_unit_tax')

    @api.depends('product_id', 'quantity')
    def _get_plastic_kg(self):
        for record in self:
            total = 0
            if record.product_id and record.quantity:
                total = record.product_id.pnt_plastic_weight * record.quantity
            record['pnt_plastic_kg'] = total
    pnt_plastic_kg = fields.Float('Plastic kg', store=True, compute='_get_plastic_kg')