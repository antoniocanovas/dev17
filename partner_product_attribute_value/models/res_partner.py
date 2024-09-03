# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    attribute_value_ids = fields.One2many('product.attribute.value', 'partner_id', string='Attribute values')
