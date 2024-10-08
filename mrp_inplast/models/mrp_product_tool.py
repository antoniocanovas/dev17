# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api
from odoo.exceptions import ValidationError


class MrpProductTool(models.Model):
    _name = "mrp.product.tool"

    def _get_product_tool_name(self):
        for record in self:
            name=""
            if record.pnt_tool_id.name: name += record.pnt_tool_id.name
            if record.pnt_accesory_id.name: name += " / " + record.pnt_accesory_id.name
            if record.pnt_blade_id.name: name += " / " + record.pnt_blade_id.name
            record['name'] = name
    name = fields.Char('Name', compute='_get_product_tool_name')


    # Datos de empresa de categoría de moldes y accesorios para usar en dominios de equipos:
    pnt_mrp_tool_categ_id = fields.Many2one('maintenance.equipment.category', store=False,
                                            default=lambda self: self.env.company.pnt_mrp_tool_categ_id)

    pnt_mrp_accesory_categ_id = fields.Many2one('maintenance.equipment.category', store=False,
                                                default=lambda self: self.env.company.pnt_mrp_accesory_categ_id)

    pnt_mrp_blade_categ_id = fields.Many2one('maintenance.equipment.category', store=False,
                                             default=lambda self: self.env.company.pnt_mrp_blade_categ_id)

    # El molde para usar en la fabricación (con o sin accesorio):
    pnt_tool_id = fields.Many2one('maintenance.equipment', string='Mold', store=True, copy=True)
    pnt_accesory_id = fields.Many2one('maintenance.equipment', string='Accesory', store=True, copy=True)
    pnt_blade_id = fields.Many2one('maintenance.equipment', string='Blade', store=True, copy=True)

    pnt_accesory_ids = fields.Many2many(related="pnt_tool_id.pnt_tool_accesory_ids")
    pnt_blade_ids = fields.Many2many(related="pnt_tool_id.pnt_tool_blade_ids")
    product_tmpl_id = fields.Many2one('product.template', string='Product')