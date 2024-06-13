# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

OPTIONS = [
    ('own', 'Own'),
    ('parent', 'My Company')
]

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Tipo de restricción: mis productos o los de mi compañía (parent_id):
    pnt_ecommerce_restriction_type = fields.Selection(selection=OPTIONS, string='Type')
    # Productos permitidos, en caso de que el tipo de restricción sea "own", usar los propios (no compañía):
    pnt_ecommerce_partner_product_ids = fields.Many2many('product.template', string="eCommerce products")
    # Usado en el form ocultando la página específica de productos permitidos:
    pnt_ecommerce_restricted = fields.Boolean('Only allowed products')

    # Método para campo no almacenado de productos permitidos en ecommerce (propios o de parent_id):
    @api.onchange("pnt_ecommerce_restriction_type","pnt_ecommerce_partner_product_ids", "parent_id")
    def _get_allowed_products(self):
        for record in self:
            if record.pnt_ecommerce_restriction_type == 'own':
                record.ecommerce_product_ids = [(6, 0, record.pnt_ecommerce_partner_product_ids.ids)]
            elif record.pnt_ecommerce_restriction_type == 'parent':
                record.ecommerce_product_ids = [(6, 0, record.parent_id.ecommerce_product_ids.ids)]
            else:
                record.ecommerce_product_ids = []
    ecommerce_product_ids = fields.Many2many('product.template',
                                             string="Allowed Products",
                                             compute="_get_allowed_products",
                                             )

    # Método ejecutado por acción de servidor contextual para habilitar / deshabilitar restricción:
    def get_ecommerce_product_visibility(self):
        for record in self:
            group = self.env.ref('website_sale_restricted_product.website_sale_all_products_group')
            user = self.env['res.users'].search([('partner_id', '=', record.id)])
            if user.id:
                if group in user.groups_id:
                    group.write({'users': [(3, user.id)]})
                    self.pnt_ecommerce_restricted = True
                else:
                    group.write({'users': [(4, user.id)]})
                    self.pnt_ecommerce_restricted = False
            else:
                raise UserError("Previous configuration required: Portal access to this contact.")
