# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.constrains("state")
    def _check_non_allowed_products_in_cart(self):
        self.ensure_one()
        if (self.website_id.id) and (self.env.user.partner_id.pnt_ecommerce_restriction_type != False):
            message = "Estos productos de tu cesta no están disponibles para tu usuario: "
            len_message = len(message)
            for li in self.order_line:
                if li.product_id.product_tmpl_id.id not in self.env.user.partner_id.ecommerce_product_ids.ids:
                    message += li.product_id.name + "; "
            if len(message) != len_message:
                raise UserError(message)
