# -*- coding: utf-8 -*-

from odoo import models, api


class AccountMove(models.Model):
    _inherit = 'account.move'



    price_update_mode = fields.Selection([('0','0'),('1','1'),('2','2')], string='PUM', default='0')

    def action_post(self):
        res = super(AccountMove, self).action_post()
        if self.move_type in ['in_invoice', 'in_refund']:
            psi_obj = self.env['product.supplierinfo']
            for l in self.invoice_line_ids:
                psi = psi_obj.search(
                    [('product_tmpl_id', '=', l.product_id.product_tmpl_id.id), ('partner_id', '=', self.partner_id.id)],
                    limit=1)
                if psi:
                    psi.write({
                        'discount': l.discount,
                        'price': l.price_unit,
                        'date_start': self.invoice_date
                    })
                else:
                    psi_obj.create({
                        'partner_id': self.partner_id.id,
                        'product_tmpl_id': l.product_id.product_tmpl_id.id,
                        'discount': l.discount,
                        'price': l.price_unit,
                        'date_start': self.invoice_date
                    })
        return res
