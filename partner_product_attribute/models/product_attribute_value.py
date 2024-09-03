# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api

class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    partner_id = fields.Many2one('res.partner', string='Partner')
