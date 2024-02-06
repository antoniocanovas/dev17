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

    # El molde para usar en la fabricación (con o sin accesorio):
    pnt_tool_id = fields.Many2one('maintenance.equipment', string='Mold', store=True, copy=True)
