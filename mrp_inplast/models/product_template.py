# Copyright 2023 Serincloud SL - Ingenieriacloud.com


from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    mrp_tool_ids = fields.One2many(
        "mrp.product.tool", "product_tmpl_id", string="Tools", copy=True
    )

    mrp_bom_template_id = fields.Many2one("product.bom.template", string="BOM Template")

    def copy(self, default: dict | None = None) -> "ProductTemplate":
        """
        Al duplicar un product.template, duplica también sus listas de materiales
        activas.
        Además, evita copiar las traducciones del nombre para que el producto
        duplicado comience limpio, como un producto nuevo.
        """
        # Llamar al método copy del padre para duplicar el producto
        new_product = super().copy(default)

        # Limpiar las traducciones del nombre del producto duplicado
        # Solo mantener el nombre en el idioma actual
        self._clear_name_translations(new_product)

        # Buscar todas las BoMs activas asociadas a este product.template
        active_boms = self.env["mrp.bom"].search(
            [("product_tmpl_id", "=", self.id), ("active", "=", True)]
        )

        # Duplicar cada BoM activa y asignarla al nuevo producto
        for bom in active_boms:
            # Crear un default específico para la BoM
            bom_default = {
                "product_tmpl_id": new_product.id,
                "product_id": False,  # Resetear product_id para que aplique
                # a todo el template
            }

            # Si la BoM original tiene un código, modificarlo para el duplicado
            if bom.code:
                bom_default["code"] = f"{bom.code}"

            # Duplicar la BoM
            bom.copy(bom_default)

        return new_product

    def _clear_name_translations(self, product: object):
        """
        Limpia las traducciones del campo 'name' de un producto,
        dejando solo el valor en el idioma por defecto de la empresa.
        Esto simula el comportamiento de un producto recién creado.
        """
        # Obtener todos los idiomas instalados
        installed_langs = self.env["res.lang"].search([("active", "=", True)])

        # Obtener el nombre actual del producto (en el idioma por defecto)
        # default_name = product.name

        # Para cada idioma, establecer el nombre al valor por defecto
        # Esto elimina efectivamente las traducciones específicas
        for lang in installed_langs:
            if lang.code != self.env.lang:  # Evitar el idioma actual
                product.with_context(lang=lang.code).write({"name": ""})
