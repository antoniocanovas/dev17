from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    pnt_sale_header = fields.Binary(
        string="Header pages", default=lambda self: self.env.company.sale_header)
    pnt_sale_header_name = fields.Char(default=lambda self: self.env.company.sale_header_name)
    pnt_sale_footer = fields.Binary(
        string="Footer pages", default=lambda self: self.env.company.sale_footer)
    pnt_sale_footer_name = fields.Char(default=lambda self: self.env.company.sale_footer_name)