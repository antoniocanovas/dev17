# -*- coding: utf-8 -*-

from odoo import models, api


class AccountMove(models.Model):
    _inherit = 'account.move'


    def action_post(self):
        res = super(AccountMove, self).action_post()
        psi_mod = self.env['product.supplierinfo']
        if self.move_type in ['in_invoice', 'in_refund']:
            for l in self.invoice_line_ids:
                if l.price_update_mode in ['1', '2']:
                    price_unit = l.product_uom_id._compute_price(l.price_unit, l.product_id.uom_id)
                    if len(l.product_id.product_tmpl_id.product_variant_ids.ids) == 1:
                        psi = psi_mod.search(
                            [('product_tmpl_id', '=', l.product_id.product_tmpl_id.id),
                             ('partner_id', '=', self.partner_id.id),
                             ('product_uom', '=', l.product_id.uom_po_id.id),
                             ('date_end', '=', False)],
                            limit=1)
                    else:
                        psi = psi_mod.search(
                            [('product_id', '=', l.product_id.id),
                             ('partner_id', '=', self.partner_id.id),
                             ('product_uom', '=', l.product_id.uom_po_id.id),
                             ('date_end', '=', False)],
                            limit=1)

                    if psi:
                        psi.write({
                            'discount': l.discount,
                            'price': l.price_unit,
                            'date_start': self.invoice_date
                        })
                    else:
                        psi_mod.create({
                            'partner_id': self.partner_id.id,
                            'product_tmpl_id': l.product_id.product_tmpl_id.id,
                            'product_id': l.product_id.id,
                            'product_uom': l.product_id.uom_po_id.id,
                            'discount': l.discount,
                            'price': price_unit,
                            'date_start': self.invoice_date,
                            'delay': 1,
                        })

                    if l.price_update_mode == '2':
                        l.product_id.standard_price = price_unit
        return res
