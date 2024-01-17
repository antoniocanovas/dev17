from odoo import _, api, fields, models
from datetime import timedelta, date
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Campos de estado de la tarifa, necesito los boolean para los filtros:
    @api.depends('state', 'order_line', 'pricelist_id.pnt_state')
    def _get_sale_pricelist_state(self):
        for record in self:
            state = record.pnt_pricelist_state
            if record.state in ['draft','sent']:
                state = record.pricelist_id.pnt_state
            record['pnt_pricelist_state'] = state
    pnt_pricelist_state = fields.Selection([('active','Active'),('update','Update'),('locked','Locked')],
                                           string='Pricelist state', store=True, copy=False,
                                           compute='_get_sale_pricelist_state')
    @api.depends('pnt_pricelist_state')
    def _get_pricelist_state_is_update(self):
        update = False
        if self.pnt_pricelist_state == 'update': update = True
        self.pnt_pricelist_is_update = update
    pnt_pricelist_is_update = fields.Boolean('Pricelist update', store=False, compute='_get_pricelist_state_is_update')

    @api.depends('pnt_pricelist_state')
    def _get_pricelist_state_is_locked(self):
        locked = False
        if self.pnt_pricelist_state == 'locked': locked = True
        self.pnt_pricelist_is_locked = locked
    pnt_pricelist_is_locked = fields.Boolean('Pricelist locked', store=False, compute='_get_pricelist_state_is_locked')




    # Restricción para que no se puedan cambiar de estado los pedidos con tarifas bloqueadas:
    @api.constrains('state')
    def __avoid_sales_with_locked_pricelist(self):
        for record in self:
            if record.pnt_pricelist_state == 'locked':
                raise UserError('Pedido bloqueado, revisa y actualiza la tarifa del cliente: ' + record.partner_id.name)
            return True
