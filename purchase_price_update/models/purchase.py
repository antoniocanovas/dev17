# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import models, api, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    price_update_mode = fields.Selection(selection=[('0','0'),('1','1'),('2','2')], string='PUM', default='0')

    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        psi_obj = self.env['product.supplierinfo']
        for l in self.order_line:
            psi = psi_obj.search(
                [('product_tmpl_id', '=', l.product_id.product_tmpl_id.id), ('partner_id', '=', self.partner_id.id)], limit=1)
            if psi:
                psi.write({
                    'discount': l.discount,
                    'price': l.price_unit,
                    'date_start': l.date_price
                })
            else:
                psi_obj.create({
                    'partner_id': self.partner_id.id,
                    'product_tmpl_id': l.product_id.product_tmpl_id.id,
                    'discount': l.discount,
                    'price': l.price_unit,
                    'date_start': l.date_price
                })
            # Precio de coste actualizado siempre a última compra (sólo para cubells, no considera distintas unidades):
#            if l.product_id.uom_po_id == l.product_uom:
#                standard_price = l.price_subtotal / l.product_uom_qty
#                l.product_id.write({'standard_price':standard_price})
        return res


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    date_price = fields.Date('Date price', default=datetime.now().date())
