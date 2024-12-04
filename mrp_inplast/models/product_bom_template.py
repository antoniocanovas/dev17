from odoo import _, api, fields, models

class ProductBomTemplate(models.Model):
    _name = "product.bom.template"
    _description = "Product bom template"

    name = fields.Char("Name")
    code = fields.Char("Sufix code")
    printed_code = fields.Char("Printed code")
    type = fields.Selection(
        [
            ("box", "Box"),
            ("pallet", "Pallet"),
            ("box_nonmrp", "Box third parties"),
            ("pallet_nonmrp", "Pallet third parties"),
        ],
        string="Packing type",
    )

    box_template_id = fields.Many2one("product.bom.template", domain="[('type','in',['box','box_nonmrp'])]")

    line_ids = fields.One2many('product.bom.template.line', 'template_id', string='Lines', copy=True)
