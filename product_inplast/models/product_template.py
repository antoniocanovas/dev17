# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError

LABELS = [
    ("standard", "Standard"),
    ("double", "Double"),
    ("sb", "San Bernardo"),
    ("buxton", "Buxton"),
    ("nestle", "Nestle"),
]


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # Tipo de productos en subfamilia:
    pnt_product_type = fields.Selection(
        [
            ("final", "End-product"),
            ("semi", "Semi-finished"),
            ("packing", "Packing"),
            ("raw", "Raw"),
            ("dye", "Dye"),
            ("packaging", "Packaging"),
            ("box", "Box"),
            ("pallet", "Pallet"),
            ("tool", "Tool"),
            ("other", "Other"),
        ],
        store=True,
        copy=True,
        string="MRP type",
    )
    pnt_parent_id = fields.Many2one("product.template", string="Main product")
    pnt_parent_qty = fields.Integer("Parent qty")
    pnt_product_dye = fields.Char(string="Product dye", store=True, copy=True, translate=True)
    pnt_product_raw = fields.Char(string="Product raw", store=True, copy=True, translate=True)
    product_base_dye = fields.Char(string=" Main product dye", copy=True, translate=True,compute="_compute_product_base_fields",)
    product_base_raw = fields.Char(string="Main product raw",  copy=True, translate=True,compute="_compute_product_base_fields",)
    pnt_net_weight = fields.Float('Net Weight', compute='_compute_net_weight', digits='Stock Weight')

    @api.depends('pnt_parent_id','pnt_parent_id.weight')
    def _compute_net_weight(self):
        for record in self:
            net_weight = record.weight
            if (record.pnt_parent_id.id) and (record.pnt_product_type in ['packing']):
                net_weight = record.pnt_parent_id.weight * record.pnt_parent_qty
            record['pnt_net_weight'] = net_weight


    pnt_box_qty = fields.Integer("Box quantity")

    pnt_product_coa = fields.Many2one(
        "pnt.coa",
        string="COA",
    )
    pnt_label_type = fields.Selection(
        selection=LABELS, string="Label type", default="standard"
    )

    pnt_customer_code_print = fields.Boolean("Customer code on label")
    pnt_customer_code_ids = fields.One2many('product.customer.code','product_tmpl_id', string='Customer codes')
    number_of_labels = fields.Integer(
        string="Number of labels", required=False, default="1"
    )

    @api.depends("name", "default_code", "pnt_product_dye")
    def _compute_display_name(self):
        for template in self:
            template.display_name = "{}{}{}".format(
                template.default_code and "[%s] " % template.default_code or "",
                template.name,
                template.pnt_product_dye and " [%s]" % template.pnt_product_dye or "",
            )

    pnt_pricelist_item_ids = fields.One2many(
        "product.pricelist.item", "product_tmpl_id", string="Pricelist items"
    )
    pnt_packing_ids = fields.One2many(
        "product.template", "pnt_parent_id", string="Packing products"
    )
    pnt_bom_line_ids = fields.One2many(
        "mrp.bom.line", "product_tmpl_id", string="BOM lines"
    )

    pnt_code = fields.Selection(
        [
            ("a", "A"),
            ("b", "B"),
            ("c", "C"),
            ("d", "D"),
            ("e", "E"),
            ("f", "F"),
            ("g", "G"),
            ("h", "H"),
            ("i", "I"),
            ("j", "J"),
            ("k", "K"),
            ("l", "L"),
            ("m", "M"),
            ("n", "N"),
            ("o", "O"),
            ("p", "P"),
            ("q", "Q"),
            ("r", "R"),
            ("s", "S"),
            ("t", "T"),
            ("u", "U"),
            ("v", "V"),
            ("w", "W"),
            ("x", "X"),
            ("y", "Y"),
            ("z", "Z"),
        ],
    string="Code"
    )

    def get_inplast_default_code(self):
        for record in self:  # Loop over each record in case multiple records are passed
            if record.pnt_product_type == "final":
                code = ""
                if record.categ_id.parent_id.pnt_code:
                    code += record.categ_id.parent_id.pnt_code
                if record.categ_id.pnt_code:
                    code += record.categ_id.pnt_code
                if record.pnt_code:
                    code += record.pnt_code.upper()
                if record.bom_ids:
                    bom = record.bom_ids[0]
                    if bom.code:
                        code += bom.code
                record.default_code = code

    default_code = fields.Char(compute="_get_inplast_default_code")
    @api.depends(
        "pnt_product_type",
        "pnt_product_dye",
        "pnt_product_raw",
        "pnt_parent_id.pnt_product_dye",
        "pnt_parent_id.pnt_product_raw",
    )
    def _compute_product_base_fields(self):
        for record in self:
            if record.pnt_product_type == "final" or record.pnt_product_type == "semi":
                # Para productos finales se usan los valores propios
                record.product_base_dye = record.pnt_product_dye
                record.product_base_raw = record.pnt_product_raw
            elif record.pnt_product_type == "packing":
                # Para productos de empaque se heredan los datos del producto padre
                record.product_base_dye = record.pnt_parent_id.pnt_product_dye if record.pnt_parent_id else ""
                record.product_base_raw = record.pnt_parent_id.pnt_product_raw if record.pnt_parent_id else ""
            else:
                # En otros casos, se pueden dejar en blanco o definir otro comportamiento
                record.product_base_dye = ""
                record.product_base_raw = ""