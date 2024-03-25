# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api

class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    set_template_id = fields.Many2one('set.template', string='Set template', store=True, copy=False)
    
    def _get_set_hidden(self):
        company_bom_attribute = self.env.user.company_id.bom_attribute_id
        set_hidden = True
        if (company_bom_attribute.id) and (company_bom_attribute.id == self.attribute_id.id): set_hidden = False
        self.set_hidden = set_hidden
    set_hidden = fields.Boolean('Set hidden', store=False, compute='_get_set_hidden')
