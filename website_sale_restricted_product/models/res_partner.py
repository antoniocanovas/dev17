# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

OPTIONS = [
    ('own', 'Own'),
    ('parent', 'My Company')
]

class ResPartner(models.Model):
    _inherit = 'res.partner'


    pnt_ecommerce_partner_product_ids = fields.Many2many('product.template', string="eCommerce products")
    #    pnt_ecommerce_restricted = fields.Boolean('Only allowed products')
    pnt_ecommerce_restriction_type = fields.Selection(selection=OPTIONS, string='Type')

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

    @api.depends('pnt_ecommerce_restriction_type')
    def get_ecommerce_product_visibility(self):
        newid = self.id
        raise UserError(newid)
        if newid:
            partnerid = int(newid.split("_")[1])
            group = self.env.ref('website_sale_restricted_product.website_sale_all_products_group')
            portaluser = self.env['res.users'].search([('partner_id', '=', partnerid)])

            if (portaluser.id) and (self.pnt_ecommerce_restriction_type not in ['own','parent']):
                group.write({'users': [(3, portaluser.id)]})
                raise UserError('quito')
            elif (portaluser.id) and (self.pnt_ecommerce_restriction_type in ['own','parent']):
                group.write({'users': [(4, portaluser.id)]})
                raise UserError('añado todos')
            else:
                raise UserError("Previous configuration required: Portal access to this contact.")
