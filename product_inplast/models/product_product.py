# Copyright 2023 Serincloud SL - Ingenieriacloud.com
from __future__ import annotations

from typing import Any

from odoo import api, models
from odoo.tools.misc import unique


class ProductProduct(models.Model):
    _inherit = "product.product"

    # Reescribimos la función estandar para poder añadir el dye como parámetro
    @api.depends("name", "default_code", "product_tmpl_id", "pnt_product_dye")
    @api.depends_context(
        "display_default_code", "seller_id", "company_id", "partner_id"
    )
    def _compute_display_name(self):
        def get_display_name(name: str, code: str, dye: str | None) -> str:
            if self._context.get("display_default_code", True) and code and dye:
                return f"[{code}] {name} {dye}"
            elif self._context.get("display_default_code", True) and code and not dye:
                return f"[{code}] {name}"
            elif dye:
                return f"{name} {dye}"
            return name

        partner_id = self._context.get("partner_id")
        if partner_id:
            partner_ids = [
                partner_id,
                self.env["res.partner"].browse(partner_id).commercial_partner_id.id,
            ]
        else:
            partner_ids = []
        company_id = self.env.context.get("company_id")

        # all user don't have access to seller and partner
        # check access and use superuser
        self.check_access_rights("read")
        self.check_access_rule("read")

        product_template_ids = self.sudo().product_tmpl_id.ids

        supplier_info_by_template = {}  # Ensure always defined
        if partner_ids:
            # prefetch the fields used by the `display_name`
            supplier_info = (
                self.env["product.supplierinfo"]
                .sudo()
                .search_fetch(
                    [
                        ("product_tmpl_id", "in", product_template_ids),
                        ("partner_id", "in", partner_ids),
                    ],
                    [
                        "product_tmpl_id",
                        "product_id",
                        "company_id",
                        "product_name",
                        "product_code",
                    ],
                )
            )
            for r in supplier_info:
                supplier_info_by_template.setdefault(r.product_tmpl_id, []).append(r)

        for product in self.sudo():
            variant: object = (
                product.product_template_attribute_value_ids._get_combination_name()
            )

            name = variant and f"{product.name} ({variant})" or product.name
            sellers = (
                self.env["product.supplierinfo"]
                .sudo()
                .browse(self.env.context.get("seller_id"))
                or []
            )
            if not sellers and partner_ids:
                product_supplier_info = supplier_info_by_template.get(
                    product.product_tmpl_id, []
                )
                sellers = [
                    x
                    for x in product_supplier_info
                    if x.product_id and x.product_id == product
                ]
                if not sellers:
                    sellers = [x for x in product_supplier_info if not x.product_id]
                # Filter out sellers based on the company. This is done afterwards for
                # a better
                # code readability. At this point, only a few sellers should remain,
                # so it should
                # not be a performance issue.
                if company_id:
                    sellers = [
                        x for x in sellers if x.company_id.id in [company_id, False]
                    ]
            if sellers:
                temp = []
                for s in sellers:
                    seller_variant = (
                        s.product_name
                        and (
                            variant
                            and f"{s.product_name} ({variant})"
                            or s.product_name
                        )
                        or False
                    )
                    temp.append(
                        get_display_name(
                            seller_variant or name,
                            s.product_code or product.default_code,
                            product.pnt_product_dye
                            if product.pnt_product_dye
                            else False,
                        )
                    )

                # => Feature drop here, one record can only have one display_name now,
                # instead separate with `,`
                # Remove this comment
                product.display_name = ", ".join(unique(temp))
            else:
                product.display_name = get_display_name(
                    name,
                    product.default_code,
                    product.pnt_product_dye if product.pnt_product_dye else False,
                )

    def get_inplast_default_code(self):
        """Método para generar código automático en variantes de producto"""
        for record in self:
            if record.product_tmpl_id.pnt_product_type in ["final", "semi"]:
                code = ""
                if record.product_tmpl_id.categ_id.parent_id.pnt_code:
                    code += record.product_tmpl_id.categ_id.parent_id.pnt_code
                if record.product_tmpl_id.categ_id.pnt_code:
                    code += record.product_tmpl_id.categ_id.pnt_code
                if record.product_tmpl_id.pnt_code:
                    code += record.product_tmpl_id.pnt_code.upper()
                if record.product_tmpl_id.bom_ids:
                    bom = record.product_tmpl_id.bom_ids[0]
                    if bom.code:
                        code += bom.code
                record.default_code = code

    def copy(self, default: object = None) -> Any:
        """
        Al duplicar un product.product (variante), evita copiar las traducciones
        del nombre para que la variante duplicada comience limpia.
        """
        # Llamar al método copy del padre para duplicar la variante
        new_variant = super().copy(default)

        # Limpiar las traducciones del nombre del producto duplicado
        self._clear_name_translations(new_variant)

        return new_variant

    def _clear_name_translations(self, product: object):
        """
        Limpia las traducciones del campo 'name' de una variante de producto,
        dejando solo el valor en el idioma por defecto de la empresa.
        Esto simula el comportamiento de un producto recién creado.
        """
        # Obtener todos los idiomas instalados
        installed_langs = self.env["res.lang"].search([("active", "=", True)])

        # Obtener el nombre actual del producto (en el idioma por defecto)
        default_name = product.name

        # Para cada idioma, establecer el nombre al valor por defecto
        # Esto elimina efectivamente las traducciones específicas
        for lang in installed_langs:
            if lang.code != self.env.lang:  # Evitar el idioma actual
                product.with_context(lang=lang.code).write({"name": default_name})

    def _on_name_translation_saved(self):
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
        for product in self.product_tmpl_id.product_variant_ids:
            if product.pnt_product_type in ["raw", "dye"]:
                # Paso 1: Buscar las líneas de BOM que tienen
                # este producto como componente
                bom_lines = self.env["mrp.bom.line"].search(
                    [("product_id", "=", product.id)]
                )

                # Obtener los BOMs únicos (las BOMs que tienen este
                # producto como componente)
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
