# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
from odoo.tools import format_datetime, formatLang


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    def _compute_price(self, product, quantity, uom, date, currency=None):

        self and self.ensure_one()
        product.ensure_one()
        uom.ensure_one()

        product_uom = product.uom_id
        if product_uom != uom:
            convert = lambda p: product_uom._compute_price(p, uom)
        else:
            convert = lambda p: p

        price = super(PricelistItem, self)._compute_price(product, quantity, uom, date,
                                       currency=None)
        if self.compute_price == 'fixed':
            if self.price_surcharge:
                price += convert(self.price_surcharge)

        return price

