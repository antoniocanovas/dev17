# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api

class SetTemplateLine(models.Model):
    _name = 'set.template.line'
    _description = 'Set Template Line'

    def _get_name(self):
        for record in self:
            record['name'] = str(record.value_id.name) + ": " + str(record.quantity)
    name = fields.Char('Name', store=False, compute='_get_name')

    set_id   = fields.Many2one('set.template', string='Set', required=True, store=True, copy=True)
    value_id = fields.Many2one('product.attribute.value', string='Value', store=True, required=True, copy=True)
    quantity = fields.Integer('Quantity', store=True, copy=True)
    attribute_id = fields.Many2one('product.attribute', related='set_id.attribute_id')