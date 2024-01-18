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

    @api.depends('order_line','state')
    def _get_update_prices_required(self):
        for record in self:
            required = False
            for li in record.order_line:
                if (li.display_type == False) and (li.product_uom_qty > li.qty_invoiced) and (li.pricelist_id.pnt_last_update > record.date_order):
                    required = True
            record['pnt_update_prices'] = required
    pnt_update_prices = fiels.Boolean('Update prices', store=False, compute='_get_update_prices_required')

    # Restricción para que no se puedan cambiar de estado los pedidos con tarifas bloqueadas:
    @api.constrains('state')
    def __avoid_sales_with_locked_pricelist(self):
        for record in self:
            if record.pnt_pricelist_state == 'locked':
                raise UserError('Pedido bloqueado, revisa y actualiza la tarifa del cliente: ' + record.partner_id.name)
            return True
