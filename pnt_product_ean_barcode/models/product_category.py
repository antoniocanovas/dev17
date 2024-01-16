# Copyright Punstsistemes SL - Puntsistemes.es


from odoo import fields, models, api
from odoo.exceptions import UserError

class ProductCategory(models.Model):
    _inherit = ["product.category"]

    pnt_ean_required = fields.Boolean(string='EAN required')
