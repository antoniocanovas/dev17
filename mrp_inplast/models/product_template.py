# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # Datos de empresa de categoría de moldes y accesorios para usar en dominios de equipos:
    def get_tool_categ(self):
        self.pnt_mrp_tool_categ_id = self.env.company.pnt_mrp_tool_categ_id.id
    pnt_mrp_tool_categ_id = fields.Many2one('maintenance.equipment.category', store=False,
                                            compute='get_tool_categ')
    def get_accesory_categ(self):
        self.pnt_mrp_accesory_categ_id = self.env.company.pnt_mrp_accesory_categ_id.id
    pnt_mrp_accesory_categ_id = fields.Many2one('maintenance.equipment.category', store=False,
                                                compute='get_accesory_categ')

    def get_blade_categ(self):
        self.pnt_mrp_blade_categ_id = self.env.company.pnt_mrp_blade_categ_id.id
    pnt_mrp_blade_categ_id = fields.Many2one('maintenance.equipment.category', store=False,
                                                compute='get_blade_categ')

    # El molde para usar en la fabricación (con o sin accesorio):
    pnt_tool_id = fields.Many2one('maintenance.equipment', string='Mold', store=True, copy=True)
    pnt_accesory_id = fields.Many2one('maintenance.equipment', string='Accesory', store=True, copy=True)
    pnt_blade_id = fields.Many2one('maintenance.equipment', string='Blade', store=True, copy=True)

    pnt_accesory_ids = fields.Many2many(related="pnt_tool_id.pnt_tool_accesory_ids")
    pnt_blade_ids = fields.Many2many(related="pnt_tool_id.pnt_tool_blade_ids")