from odoo import _, api, fields, models
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    pnt_move_plastic_tax_id = fields.Many2one('account.move', store=True, string='Plastic tax entry')

    @api.constrains('state')
    def _check_plastic_tax_required(self):
        for record in self:
            if (record.move_type in ['in_invoice', 'in_refund']) and (record.state in ['posted']):
                if (not record.partner_id.country_id.id):
                    raise UserError('Pon el país al proveedor para poder controlar el impuesto al plástico.')
                elif (record.partner_id.country_id.code != 'ES') and not (record.pnt_move_plastic_tax_id.id):
                    plastic_tax_required = False
                    for li in record.invoice_line_ids:
                        if li.product_id.pnt_plastic_weight != 0:
                            message = "El producto: " + li.product_id.name + " requiere impuesto al plástico, crea o asigna el apunte correspondiente en esta factura"
                            raise UserError(message)

            if (record.move_type in ['out_invoice', 'out_refund']) and (record.state in ['posted']):
                if (not record.partner_id.country_id.id):
                    raise UserError('Pon el país al cliente para poder controlar el impuesto al plástico.')
                elif (record.partner_id.country_id.code != 'ES') and not (record.pnt_move_plastic_tax_id.id):
                    plastic_tax_required = False
                    for li in record.invoice_line_ids:
                        if li.product_id.pnt_plastic_weight != 0:
                            message = "El producto: " + li.product_id.name + " es susceptible de recuperar el impuesto al plástico, crea o asigna el apunte correspondiente en esta factura"
                            raise UserError(message)
