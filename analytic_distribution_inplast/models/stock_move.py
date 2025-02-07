from odoo import fields, models
class StockMove(models.Model):
    _inherit = 'stock.move'

    bom_template_type = fields.Selection(
        string="Tipo de BOM Template",
        related="product_id.bom_ids.mrp_bom_template_id.type",
        store=True
    )
