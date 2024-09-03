# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api

class ProductTemplateAttributeLine(models.Model):
    _inherit = 'product.template.attribute.line'

    partner_id = fields.Many2one('res.partner', related='product_tmpl_id.manufacturer_id')
