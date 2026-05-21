# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from typing import Any

from odoo import api, fields, models

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
            ("additive", "Additive"),
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
    pnt_product_dye = fields.Char(
        string="Product dye", store=True, copy=True, translate=True
    )
    pnt_product_raw = fields.Char(
        string="Product raw", store=True, copy=True, translate=True
    )
    product_base_dye = fields.Char(
        string=" Main product dye",
        copy=True,
        translate=True,
        compute="_compute_product_base_fields",
        store=True,
    )
    product_base_raw = fields.Char(
        string="Main product raw",
        copy=True,
        translate=True,
        compute="_compute_product_base_fields",
        store=True,
    )
    pnt_net_weight = fields.Float("Net Weight", digits="Stock Weight")

    @api.depends("pnt_parent_id.weight")
    def _compute_weight(self) -> None:
        for record in self:
            record._compute_net_weight()
            self.env.flush_all()
            record._compute_gross_weight()

    def _compute_net_weight(self) -> None:
        for record in self:
            net_weight = record.weight
            if (record.pnt_parent_id.id) and (record.pnt_product_type in ["packing"]):
                net_weight = record.pnt_parent_id.weight * record.pnt_parent_qty
            record["pnt_net_weight"] = net_weight

    @api.depends(
        "bom_ids.bom_line_ids.weight",
        "bom_ids.bom_line_ids.product_id.weight",
    )
    def _compute_gross_weight(self) -> None:
        # Modelo esperado: product.template o product.product (funciona para ambos)
        # Recorre los productos seleccionados y calcula el peso total del BoM.
        # - Si la línea está en UoM de 'Peso': suma la cantidad convertida a kg.
        # - Si la línea está en UoM de 'Unidad': suma (peso del componente en kg)
        # * (cantidad).
        # - Otras categorías (longitud, volumen, etc.) se ignoran por seguridad
        # (puedes ajustar).

        uom_weight_categ = self.env.ref(
            "uom.product_uom_categ_kgm"
        )  # Categoría de peso
        kg_uom = self.env.ref("uom.product_uom_kgm")  # UoM kilogramo

        for product in self:
            is_packing = product.pnt_product_type in ["packing"]
            is_handle = product.categ_id and product.categ_id.type == "handle"
            if not (is_packing or is_handle):
                continue

            # Obtener un BoM válido (si tienes varios, coge el primero como
            # en tu código original)
            bom = product.bom_ids[:1]
            if not bom:
                if is_handle:
                    gross_weight = product.pnt_net_weight or 0.0
                    if product._name == "product.product":
                        product.product_tmpl_id.write({"weight": gross_weight})
                    else:
                        product.write({"weight": gross_weight})
                continue
            bom = bom[0]

            bom_lines = bom.bom_line_ids
            if not bom_lines:
                if is_handle:
                    gross_weight = product.pnt_net_weight or 0.0
                    if product._name == "product.product":
                        product.product_tmpl_id.write({"weight": gross_weight})
                    else:
                        product.write({"weight": gross_weight})
                continue

            total_weight = 0.0

            for line in bom_lines:
                # UoM de la línea
                line_uom = line.product_uom_id or line.product_id.uom_id

                if line_uom and line_uom.category_id == uom_weight_categ:
                    # La cantidad YA es un peso: conviértela a kg y súmala
                    # directamente
                    qty_in_kg = line_uom._compute_quantity(line.product_qty, kg_uom)
                    total_weight += qty_in_kg
                else:
                    # Trátalo como unidades (u otra categoría): usa el peso
                    # del componente * cantidad
                    component = line.product_id
                    if not component:
                        continue
                    component_weight = component.weight or 0.0
                    quantity = line.product_qty or 0.0  # cantidad en unidades
                    total_weight += component_weight * quantity

            if is_handle:
                gross_weight = (product.pnt_net_weight or 0.0) + total_weight
            else:
                gross_weight = total_weight

            # Escribe el total en el campo 'weight' del producto (en kg)
            # Para product.product, conviene escribir en la plantilla:
            if product._name == "product.product":
                product.product_tmpl_id.write({"weight": gross_weight})
            else:
                product.write({"weight": gross_weight})

    pnt_box_qty = fields.Integer("Box quantity")

    pnt_product_two_sscc = fields.Boolean("Two SSCC codes")

    pnt_product_coa = fields.Many2one(
        "pnt.coa",
        string="COA",
    )
    pnt_label_type = fields.Selection(
        selection=LABELS, string="Label type", default="standard"
    )

    pnt_customer_code_print = fields.Boolean("Customer code on label")
    pnt_production_label_note = fields.Text(string="Production label note")
    pnt_customer_code_ids = fields.One2many(
        "product.customer.code",
        "product_tmpl_id",
        string="Customer codes",
        help="Estos codigos son los que se imprimen en los informes de los productos,"
        " si se quiere modificar el codigo para buscar en la linea de ventas accede"
        " a la ventana de ventas del producto y configurelo ahí.",
    )
    number_of_labels = fields.Integer(
        string="Number of labels", required=False, default="1"
    )

    @api.depends("name", "default_code", "pnt_product_dye")
    def _compute_display_name(self) -> None:
        for template in self:
            template.display_name = "{}{}{}".format(
                template.default_code and f"[{template.default_code}] " or "",
                template.name,
                template.pnt_product_dye and f" [{template.pnt_product_dye}]" or "",
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
        string="Code",
    )

    def get_inplast_default_code(self) -> None:
        for record in self:  # Loop over each record in case multiple records are passed
            if record.pnt_product_type in ["final", "semi"]:
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
    def _compute_product_base_fields(self) -> None:
        # Obtener idiomas instalados
        langs = self.env["res.lang"].search([("active", "=", True)]).mapped("code")

        for record in self:
            # Determinar el origen de los datos según el tipo de producto
            source_dye = ""
            source_raw = ""
            source_record = None

            if record.pnt_product_type in ["final", "semi"]:
                # Para productos finales se usan los valores propios
                source_dye = record.pnt_product_dye or ""
                source_raw = record.pnt_product_raw or ""
                source_record = record
            elif record.pnt_product_type == "packing":
                # Para productos de empaque se heredan los datos del producto padre
                if record.pnt_parent_id:
                    source_dye = record.pnt_parent_id.pnt_product_dye or ""
                    source_raw = record.pnt_parent_id.pnt_product_raw or ""
                    source_record = record.pnt_parent_id

            # Actualizar valores en el idioma actual
            record.product_base_dye = source_dye
            record.product_base_raw = source_raw

            # Copiar traducciones de los campos fuente si hay un registro origen
            if source_record:
                for lang in langs:
                    if lang != self.env.context.get("lang", "en_US"):
                        source_with_lang = source_record.with_context(lang=lang)
                        record.with_context(lang=lang).write(
                            {
                                "product_base_dye": source_with_lang.pnt_product_dye
                                or "",
                                "product_base_raw": source_with_lang.pnt_product_raw
                                or "",
                            }
                        )

    def _on_name_translation_saved(self) -> None:
        """
        Método llamado automáticamente cuando se guarda una traducción
        del campo 'name' desde el wizard de traducción.

        Actualiza las BOMs que contienen este producto como componente
        y las BOMs de nivel superior.
        """
        self.ensure_one()

        # Actualizar display_name
        self._compute_display_name()

        # Obtener todos los product.product de este template
        for product in self.product_variant_ids:
            if product.pnt_product_type in ["raw", "dye"]:
                # Paso 1: Buscar las líneas de BOM que tienen este producto
                # como componente
                bom_lines = self.env["mrp.bom.line"].search(
                    [("product_id", "=", product.id)]
                )

                # Obtener los BOMs únicos (las BOMs que tienen este producto
                # como componente)
                boms_step1 = bom_lines.mapped("bom_id")

                # Ejecutar bom_product_color_and_raw_update() para cada BOM del paso 1
                for bom in boms_step1:
                    bom.bom_product_color_and_raw_update()

                # Paso 2: Buscar las BOMs que tienen como componente
                # los product_template
                # que se producen en las BOMs del paso 1
                if boms_step1:
                    product_templates_step1 = boms_step1.mapped("product_tmpl_id")
                    parent_bom_lines = self.env["mrp.bom.line"].search(
                        [
                            (
                                "product_id.product_tmpl_id",
                                "in",
                                product_templates_step1.ids,
                            )
                        ]
                    )
                    boms_step2 = parent_bom_lines.mapped("bom_id")

                    # Actualizar también las BOMs del paso 2
                    for bom in boms_step2:
                        bom.bom_product_color_and_raw_update()

    def write(self, vals: dict[str, Any]) -> bool:
        """
        Sobrescribe write para detectar cambios en el campo 'name'
        incluyendo cuando se guardan traducciones
        """
        result = super().write(vals)

        # Detectar si se está modificando el campo 'name'
        # Esto incluye tanto cambios directos como traducciones
        if "name" in vals:
            for record in self:
                record._on_name_translation_saved()

        return result
