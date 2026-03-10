# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    pnt_raw_type_id = fields.Many2one("uom.category", string="Distribution type")
    # Cambio a related (19/02/25) borrar en un futuro la línea comentada:
    # mrp_bom_template_id = fields.Many2one('product.bom.template', string='BOM
    # Template')
    mrp_bom_template_id = fields.Many2one(related="product_tmpl_id.mrp_bom_template_id")
    pnt_product_type = fields.Selection(related="product_tmpl_id.pnt_product_type")

    # Campo para poder utilizar en el dominio de asignación para mrp_tool_id:
    mrp_tool_product_tmpl_id = fields.Many2one(
        'product.template',
        string='MRP Product tool',
        compute='_get_mrp_tool_product_tmpl_id'
    )

    def _get_mrp_tool_product_tmpl_id(self):
        for record in self:
            product_tmpl = record.product_tmpl_id
            if record.product_tmpl_id.pnt_parent_id.id:
                product_tmpl = record.product_tmpl_id.pnt_parent_id
            record['mrp_tool_product_tmpl_id'] = product_tmpl.id


    # Método interno para ser llamado desde una BA, para los casos de
    #  Lista de Materiales por %
    def bom_percent_update(self):
        for record in self:
            if record.pnt_raw_type_id.id:
                uom_ref = self.env["uom.uom"].search(
                    [
                        ("category_id", "=", record.pnt_raw_type_id.id),
                        ("uom_type", "=", "reference"),
                    ]
                )
                bom_qty = record.pnt_raw_qty
                for li in record.bom_line_ids:
                    if (li.pnt_raw_percent != 0) and (
                        li.product_uom_category_id == li.pnt_raw_type_id
                    ):
                        factor = uom_ref._compute_quantity(
                            bom_qty, li.product_id.uom_id
                        )
                        li["product_qty"] = li.pnt_raw_percent / 100 * factor
                    if (li.pnt_raw_percent == 0) and (
                        li.product_uom_category_id == li.pnt_raw_type_id
                    ):
                        li["product_qty"] = 0.0

    @api.depends("product_tmpl_id", "pnt_raw_type_id")
    def _get_default_uom(self):
        uom = self.env["uom.uom"].search(
            [
                ("category_id", "=", self.pnt_raw_type_id.id),
                ("uom_type", "=", "reference"),
            ]
        )
        self.pnt_raw_uom_id = uom.id

    pnt_raw_uom_id = fields.Many2one(
        "uom.uom", string="UOM", store=True, compute="_get_default_uom"
    )

    @api.depends("product_id")
    def _get_uom_available(self):
        weight = self.env.ref("uom.product_uom_categ_kgm")
        volume = self.env.ref("uom.product_uom_categ_vol")
        self.pnt_raw_available_ids = [(6, 0, [weight.id, volume.id])]

    pnt_raw_available_ids = fields.Many2many(
        "uom.category", string="Raw types available", compute="_get_uom_available"
    )

    # Cantidad de producto (peso o volumen) a distribuir entre productos
    # de esta categoría según product.template:
    @api.depends(
        "product_tmpl_id",
        "product_uom_id",
        "product_tmpl_id.weight",
        "product_tmpl_id.pnt_parent_id.weight",
        "product_tmpl_id.volume",
        "product_qty",
        "pnt_raw_type_id",
    )
    def _get_product_raw_qty(self):
        for record in self:
            qty = 0
            # factor = unidad_origen(cantidad_origen, unidad_destino)
            factor = record.product_uom_id._compute_quantity(
                record.product_qty, record.product_tmpl_id.uom_id
            )
            if record.pnt_raw_type_id == self.env.ref("uom.product_uom_categ_kgm"):
                if record.product_tmpl_id.pnt_product_type == "packing":
                    qty = record.product_tmpl_id.pnt_net_weight * factor
                else:
                    qty = record.product_tmpl_id.weight * factor
            if record.pnt_raw_type_id == self.env.ref("uom.product_uom_categ_vol"):
                qty = record.product_tmpl_id.volume * factor
            record["pnt_raw_qty"] = qty

    pnt_raw_qty = fields.Float(
        "UOM Qty", store=True, compute="_get_product_raw_qty", digits="Stock Weight"
    )

    @api.depends("bom_line_ids")
    def compute_box_line_id(self):
        for record in self:
            box_line = self.env["mrp.bom.line"].search(
                [
                    ("bom_id", "=", record.id),
                    ("product_id.pnt_product_type", "=", "box"),
                ],
                limit=1,
            )
            record.box_line_id = box_line.id

    box_line_id = fields.Many2one(
        "mrp.bom.line", compute="compute_box_line_id", store=True, index=True
    )
    box_id = fields.Many2one(
        "product.product", related="box_line_id.product_id", index=True
    )
    box_count = fields.Float("Box count", related="box_line_id.product_qty")

    @api.depends("bom_line_ids")
    def compute_pallet_line_id(self):
        for record in self:
            pallet_line = self.env["mrp.bom.line"].search(
                [
                    ("bom_id", "=", record.id),
                    ("product_id.pnt_product_type", "=", "pallet"),
                ],
                limit=1,
            )
            record.pallet_line_id = pallet_line.id

    pallet_line_id = fields.Many2one(
        "mrp.bom.line", compute="compute_pallet_line_id", store=True, index=True
    )
    pallet_id = fields.Many2one(
        "product.product", related="pallet_line_id.product_id", index=True
    )
    pallet_count = fields.Float("Pallet count", related="pallet_line_id.product_qty")

    mrp_tool_id = fields.Many2one("mrp.product.tool", string="Tool")

    def _update_field_with_translations(
        self,
        target_field: str,
        source_products: models.Model,
        product_type_field: str,
        fallback_field: str,
    ) -> dict:
        """
        Actualiza un campo con traducciones basándose en productos de origen.

        :param target_field: Campo a actualizar (ej: 'pnt_product_dye')
        :param source_products: Recordset de productos fuente
        :param product_type_field: Tipo de producto principal (ej: 'dye', 'raw')
        :param fallback_field: Campo alternativo si no es tipo principal
        :return: Diccionario con traducciones {lang: value}
        """
        # Obtener idiomas instalados
        langs = self.env["res.lang"].search([("active", "=", True)]).mapped("code")

        translations = {}
        for lang in langs:
            value = ""
            if len(source_products) == 1:
                # Para 1 producto: obtener su traducción en el idioma actual
                product_tmpl = source_products.product_id.product_tmpl_id.with_context(
                    lang=lang
                )
                product = source_products.product_id.with_context(lang=lang)
                if product_tmpl.pnt_product_type == product_type_field:
                    value = product.name or ""
                elif product_tmpl[fallback_field]:
                    value = product_tmpl[fallback_field] or ""

            elif len(source_products) == 2:
                # Para 2 productos: concatenar traducciones en el idioma actual
                names = []
                for line in source_products:
                    product_tmpl = line.product_id.product_tmpl_id.with_context(
                        lang=lang
                    )
                    product = line.product_id.with_context(lang=lang)
                    if product_tmpl.pnt_product_type == product_type_field:
                        # Si es tipo principal (dye/raw), usar el nombre traducido
                        names.append(product.name or "")
                    elif product_tmpl[fallback_field]:
                        # Si es semi, usar el campo traducido (pnt_product_dye/raw)
                        names.append(product_tmpl[fallback_field] or "")
                    else:
                        names.append("")
                # Concatenar ambos nombres en el idioma actual
                value = names[0] + " + " + names[1]

            elif len(source_products) > 2:
                # Para MULTICOLOR y MULTIRAWS, mantener el texto en inglés
                # ya que es un código, no una traducción
                value = "MULTICOLOR" if product_type_field == "dye" else "MULTIRAWS"

            translations[lang] = value

        return translations

    def bom_product_color_and_raw_update(self) -> None:  # noqa: C901
        for record in self:
            colors = self.env["mrp.bom.line"].search(
                [
                    ("bom_id", "=", record.id),
                    ("product_id.pnt_product_type", "in", ["dye", "semi"]),
                ]
            )
            raws = self.env["mrp.bom.line"].search(
                [
                    ("bom_id", "=", record.id),
                    ("product_id.pnt_product_type", "in", ["raw", "semi"]),
                ]
            )

            # Actualizar pnt_product_dye con traducciones
            if colors:
                dye_translations = self._update_field_with_translations(
                    "pnt_product_dye", colors, "dye", "pnt_product_dye"
                )
                # Actualizar el valor por defecto (idioma del sistema)
                default_value = dye_translations.get(
                    self.env.context.get("lang", "en_US"), ""
                )
                if default_value:
                    record.product_tmpl_id.write({"pnt_product_dye": default_value})
                    # Actualizar traducciones para todos los idiomas
                    for lang, value in dye_translations.items():
                        if value and lang != self.env.context.get("lang", "en_US"):
                            record.product_tmpl_id.with_context(lang=lang).write(
                                {"pnt_product_dye": value}
                            )

            # Actualizar pnt_product_raw con traducciones
            if raws:
                raw_translations = self._update_field_with_translations(
                    "pnt_product_raw", raws, "raw", "pnt_product_raw"
                )
                # Actualizar el valor por defecto (idioma del sistema)
                default_value = raw_translations.get(
                    self.env.context.get("lang", "en_US"), ""
                )
                if default_value:
                    record.product_tmpl_id.write({"pnt_product_raw": default_value})
                    # Actualizar traducciones para todos los idiomas
                    for lang, value in raw_translations.items():
                        if value and lang != self.env.context.get("lang", "en_US"):
                            record.product_tmpl_id.with_context(lang=lang).write(
                                {"pnt_product_raw": value}
                            )
