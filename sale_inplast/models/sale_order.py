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
    def _avoid_sales_with_locked_pricelist_and_final_products(self):
        for record in self:
            if record.pnt_pricelist_state == 'locked':
                raise UserError('Pedido bloqueado, revisa y actualiza la tarifa del cliente: ' + record.partner_id.name)
            if (record.pnt_update_prices) and (record.state in ['sent','draft','sale']):
                raise UserError('Precios obsoletos, se requiere actualizar precios para: ' + record.partner_id.name)
            for li in record.order_line:
                if (li.product_id.pnt_product_type == 'final') and (record.state in ['sent','sale']):
                    raise UserError('Pedido con producto final, cámbialo por uno tipo PACKING (caja o palet).')

            else: return True


    # Cambiar las líneas de venta de tapones sueltos por CAJAS o PALETS, si tienen packaging asignado:
    def update_order_lines_with_related_box_pallet_products(self):
        for li in self.order_line:
            if li.product_packaging_id.id:
                pppackaging = self.env['product.product'].search(
                    [('pnt_parent_id', '=', li.product_id.product_tmpl_id.id),
                     ('pnt_parent_qty', '=', li.product_packaging_id.qty),
                     ('mrp_bom_template_id','=',li.product_packaging_id.mrp_bom_template_id.id),
                     ('pnt_product_type','=','packing')
                     ], limit=1)
                mrppackaging = self.env['product.packaging'].search(
                    [('product_id','=',pppackaging.id),('qty','=',1)])
                if pppackaging.id and mrppackaging.id:
                    price = li.price_unit * li.product_uom_qty / li.product_packaging_qty
                    qty = li.product_packaging_qty
                    li.write({'product_id': pppackaging.id, 'product_uom_qty': qty, 'price_unit': price,
                              'product_packaging_id': mrppackaging.id, 'product_packaging_qty': qty,
                              })
