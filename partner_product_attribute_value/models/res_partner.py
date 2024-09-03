# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    attribute_value_ids = fields.One2many('product.attribute.value', 'partner_id', string='Attribute values')
    attribute_value_count = fields.Integer('Values', compute='_get_attribute_value_count')

    def _get_attribute_value_count(self):
        self.attribute_value_count = len(self.attribute_value_ids.ids)
