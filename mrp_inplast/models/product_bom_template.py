from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProductBomTemplate(models.Model):
    _name = "product.bom.template"
    _description = "Product bom template"

    # Campos generales
    name = fields.Char("Name")
    pnt_type = fields.Selection(
        [
            ("box", "Box"),
            ("pallet", "Pallet from boxes"),
            ("palletmat", "Pallet from materials"),
        ],
        string="Packing type",
    )

    line_ids = fields.One2many('product.bom.template.line', 'template_id', string='Lines')






    # Cajas:

    pnt_box_type_id = fields.Many2one(
        "product.template", string="Box", domain="[('pnt_product_type','=','box')]"
    )
    ##pnt_box_base_qty = fields.Integer("Base qty")
    pnt_box_bag_id = fields.Many2one(
        "product.template",
        string="Box Bag",
        domain="[('pnt_product_type','=','packaging')]",
        default=lambda self: self.env.company.pnt_box_bag_id.id,
    )
    pnt_box_bag_qty = fields.Integer("Bags qty", default="1")
    pnt_box_label_id = fields.Many2one(
        "product.template",
        string="Box Label",
        domain="[('pnt_product_type','=','packaging')]",
    )
    pnt_box_label_qty = fields.Integer("Label qty", default="1")
    pnt_box_seal_id = fields.Many2one(
        "product.template",
        string="Box Seal",
        domain="[('pnt_product_type','=','packaging')]",
    )
    pnt_box_seal_qty = fields.Integer("Seal qty")

    # Palets:
    pnt_pallet_type_id = fields.Many2one(
        "product.template",
        string="Pallet",
        domain="[('pnt_product_type','=','pallet')]",
    )
    pnt_pallet_qty = fields.Integer("Pallet qty", default="1")
    pnt_pallet_box_id = fields.Many2one(
        "product.template",
        string="Pallet box",
        domain="[('pnt_product_type','=','box')]",
    )
    pnt_pallet_box_qty = fields.Integer("Box qty", default="24")
    ## pnt_pallet_base_qty = fields.Integer(
    ##      "Base qty", store=True, readonly=False, compute="_get_pallet_base_qty"
    ## )
    pnt_pallet_film_id = fields.Many2one(
        "product.template",
        string="Pallet Film",
        domain="[('pnt_product_type','=','packaging')]",
    )
    pnt_pallet_film_qty = fields.Integer("Film qty")
    pnt_pallet_seal_id = fields.Many2one(
        "product.template",
        string="Pallet seal",
        domain="[('pnt_product_type','=','packaging')]",
    )
    pnt_pallet_seal_qty = fields.Integer("Pallet seal qty")
    pnt_pallet_label_id = fields.Many2one(
        "product.template",
        string="Pallet Label",
        domain="[('pnt_product_type','=','packaging')]",
    )
    pnt_pallet_label_qty = fields.Integer("Pallet Label qty", default="1")
    pnt_picking_label_id = fields.Many2one(
        "product.template",
        string="Picking Label",
        domain="[('pnt_product_type','=','packaging')]",
    )
    pnt_picking_label_qty = fields.Integer("Picking Label qty", default="1")

    @api.depends("pnt_pallet_box_qty", "pnt_pallet_box_id")
    def _get_pallet_base_qty(self):
        for record in self:
            qty = 0
            if record.pnt_type == "pallet":
                qty = (
                    record.pnt_pallet_box_qty * record.pnt_pallet_box_id.pnt_parent_qty
                )
            record["pnt_pallet_base_qty"] = qty
