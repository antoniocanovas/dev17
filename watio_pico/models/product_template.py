# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api

class ProductTemplate(models.Model):
    _inherit = "product.template"

    wp_type = fields.Selection([('wp','Watio pico'),('wh','Watio hora'),('charger','Charger')], store=True)
