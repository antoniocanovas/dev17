from odoo import _, api, fields, models
from datetime import datetime
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Campos de estado de la tarifa:
    @api.depends('state', 'order_line', 'pricelist_id.pnt_state')
    def _get_sale_pricelist_state(self):
        for record in self:
            state = record.pnt_pricelist_state
            if (record.state in ['draft','sent']) and (record.invoice_status in ['no','to_invoice']):
                state = record.pricelist_id.pnt_state
            record['pnt_pricelist_state'] = state
    pnt_pricelist_state = fields.Selection([('active','Active'),('update','Update'),('locked','Locked')],
                                           string='Pricelist state', store=True, copy=False,
                                           compute='_get_sale_pricelist_state')

    pnt_last_price_update = fields.Datetime('Last price update', default=lambda self: datetime.now())

    def pnt_action_update_prices(self):
        for record in self:
            record.action_update_prices()
            record['pnt_last_price_update'] = datetime.now()


    @api.depends('order_line','state')
    def _get_sale_update_prices_required(self):
        for record in self:
            required = False
            last_update = record.pricelist_id.pnt_last_update
            if (record.invoice_status in ['no','to_invoice']) and (last_update) and (record.pnt_last_price_update < last_update):
                required = True
            record['pnt_update_prices'] = required
    pnt_update_prices = fields.Boolean('Update prices', store=False, compute='_get_sale_update_prices_required')

    # Restricción para que no se puedan cambiar de estado los pedidos con tarifas bloqueadas:
    @api.constrains('state')
    def _avoid_sales_with_locked_pricelist(self):
        for record in self:
            if record.pnt_pricelist_state == 'locked':
                raise UserError('Pedido bloqueado, revisa y actualiza la tarifa del cliente: ' + record.partner_id.name)
            if (record.pnt_update_prices) and (record.state in ['sent','draft','sale']):
                raise UserError('Precios obsoletos, se requiere actualizar precios para: ' + record.partner_id.name)
            else: return True