# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.constrains('state')
    def avoid_win_without_required_fields(self):
        for record in self:
            requirements = True
            partner = record.partner_id
            if (record.state == 'sale'):
                if not (partner.vat) or not (partner.street) or not (partner.state_id.id) or not (partner.zip):
                    requirements = False
                if not (partner.phone) and not (partner.mobile):
                    requirements = False
            if requirements == False:
                raise UserError('Es obligatorio documentar un teléfono, dirección y NIF antes de confirmar la venta.')
