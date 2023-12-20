from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    pnt_product_ids = fields.Many2many('product.product', store=False, string='Pricelist products',
                                   related='move_id.pricelist_id.pnt_product_ids')

    # Campos relativos al impuesto del plático:
    @api.depends('product_id', 'product_uom_qty')
    def _get_plastic_unit_tax(self):
        for record in self:
            total = 0
            if record.product_id and record.product_uom_qty:
                total = record.product_id.pnt_plastic_unit_tax * record.quantity
            record['pnt_plastic_tax'] = total
    pnt_plastic_tax = fields.Float('Unit tax', store=False, compute='_get_plastic_unit_tax')
