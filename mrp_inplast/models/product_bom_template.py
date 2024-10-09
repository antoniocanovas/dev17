from odoo import _, api, fields, models

class ProductBomTemplate(models.Model):
    _name = "product.bom.template"
    _description = "Product bom template"

    name = fields.Char("Name")
    code = fields.Char("Sufix code")
    type = fields.Selection(
        [
            ("box", "Box"),
            ("pallet", "Pallet"),
        ],
        string="Packing type",
    )

    line_ids = fields.One2many('product.bom.template.line', 'template_id', string='Lines')
