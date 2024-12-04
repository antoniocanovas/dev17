from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    sscc_qty = fields.Integer(string="Numbers of SSCC")
    mrp_bom_template_ids = fields.Many2many('product.bom.template', string='BOM Templates')