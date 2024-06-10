# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import models, api, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'


    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        psi_mod = self.env['product.supplierinfo']
        for l in self.order_line:
            if l.price_update_mode in ['1','2']:
                if len(l.product_id.product_tmpl_id.product_variant_ids.ids) == 1:
                    psi = psi_mod.search(
                        [('product_tmpl_id', '=', l.product_id.product_tmpl_id.id),
                         ('partner_id', '=', self.partner_id.id),
                         ('product_uom', '=', l.product_uom.id)],
                        limit=1)
                else:
                    psi = psi_mod.search(
                        [('product_id', '=', l.product_id.id),
                         ('partner_id', '=', self.partner_id.id),
                         ('product_uom', '=', l.product_uom.id)],
                        limit=1)

                if psi:
                    psi.write({
                        'discount': l.discount,
                        'price': l.price_unit,
                        'date_start': l.date_price
                    })
                else:
                    psi_mod.create({
                        'partner_id': self.partner_id.id,
                        'product_tmpl_id': l.product_id.product_tmpl_id.id,
                        'product_id': l.product_id.id,
                        'product_uom': l.product_uom.id,
                        'discount': l.discount,
                        'price': l.price_unit,
                        'date_start': l.date_price,
                        'delay': 1,
                    })

                if l.price_update_mode == '2':
                    l.product_id.standard_price = l.price_unit
        return res
