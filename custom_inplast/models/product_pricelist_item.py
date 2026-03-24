# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"


    # Campos de migración facilitados por el cliente, se pueden eliminar en un futuro:
    mig_codigopalet = fields.Char('mig_codigopalet')
