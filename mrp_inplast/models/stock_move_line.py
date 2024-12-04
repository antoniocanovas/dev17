from odoo import _, api, fields, models

class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    mrp_bom_template_id = fields.Many2one("product.bom.template", related='production_id.bom_id.mrp_bom_template_id')
