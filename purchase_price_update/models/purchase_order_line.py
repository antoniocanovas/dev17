# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import models, api, fields


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    date_price = fields.Date('Date price', default=datetime.now().date())
    price_update_mode = fields.Selection([('0','0'),('1','1'),('2','2')], string='PUM', default='0',
                                         help='0: No changes,'
                                              '1: Update pricelist on supplier,'
                                              '2: Update supplier price and product cost.'
                                         )
