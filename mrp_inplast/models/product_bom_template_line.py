from odoo import _, api, fields, models


class ProductBomTemplate(models.Model):
    _name = "product.bom.template.line"
    _description = "Product bom template line"


    name = fields.Char("Name", related='product_id.name')
    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Float('Quantity')
    template_id = fields.Many2one('product.bom.template', string='Template')

    # Tipo de productos en subfamilia:
    mrp_type = fields.Selection(
        [
            ("final", "End-product"),
            ("semi", "Semi-finished"),
            ("packing", "Packing"),
            ("raw", "Raw"),
            ("dye", "Dye"),
            ("packaging", "Packaging"),
            ("box", "BOX"),
            ("pallet", "Pallet"),
        ],
        store=True,
        copy=True,
        string="MRP type",
    )
