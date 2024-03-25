# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api

class SetTemplate(models.Model):
    _name = 'set.template'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Set Template'

    name = fields.Char(string='Nombre', required=True, store=True, copy=True)
    code = fields.Char(string='Code', required=True, store=True, copy=False)

    #    def _get_size_attribute(self):
    #        self.attribute_id = self.env.user.company_id.size_attribute_id.id
    attribute_id = fields.Many2one('product.attribute', string='Size Attribute', store=False,
                                   default=lambda self: self.env.user.company_id.size_attribute_id)
    line_ids = fields.One2many('set.template.line', 'set_id', string='Lines', store=True, copy=True)