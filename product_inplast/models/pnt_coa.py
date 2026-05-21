from odoo import fields, models

TYPE = [
    ("normal", "estandar"),
    ("asas", "asa"),
    ("nmp", "NMP"),
    ("buxton", "Buxton"),
]


class PntCoa(models.Model):
    _name = "pnt.coa"
    _description = "COA fields"

    name = fields.Char(string="Name")
    type = fields.Selection(selection=TYPE, default="normal")
    print_multicolor = fields.Boolean(
        "Multicolor", help="Show the Multicolor Body image field in COA contents"
    )
    print_quality_meassure = fields.Boolean(
        "Quality meassures", help="Show quality measures attachment in COA reports"
    )
    print_components = fields.Boolean(
        "Components", help="Show the Components Body image field in COA contents"
    )

    material_number = fields.Char("Material Number")
    specification_number = fields.Char("Specifitacion Number")
    vendor_site_number = fields.Char("Vendor Site Number")
    denomination = fields.Char("Denomination")

    language_selection = fields.Selection(
        selection="_get_available_languages",
        string="Select Language",
        default=lambda self: self.env.lang,
    )

    content_ids = fields.One2many("pnt.coa.content", "coa_id", string="COA Contents")

    def _get_available_languages(self):
        """Obtiene los idiomas configurados en Odoo y los devuelve como
        opciones para selección."""
        languages = self.env["res.lang"].search([("active", "=", True)])
        return [(lang.code, lang.name) for lang in languages]

    def create(self, vals: dict) -> models.Model:
        """Crea automáticamente registros de contenido COA para cada
        idioma configurado."""
        # Crea el registro principal de COA
        coa_record = super().create(vals)

        # Obtiene todos los idiomas activos en Odoo
        active_languages = self.env["res.lang"].search([("active", "=", True)])

        # Crea un registro de contenido por cada idioma
        for lang in active_languages:
            self.env["pnt.coa.content"].create(
                {
                    "coa_id": coa_record.id,
                    "language_code": lang.code,
                    "coa_body": False,
                    "multicolor_body": False,
                    "components_body": False,
                    "table_batch_certificate": False,
                }
            )

        return coa_record

    def get_coa_body_for_partner_lang(self, partner_lang: str) -> str:
        """Obtiene el contenido COA body adecuado basado en el idioma del partner."""
        self.ensure_one()
        content = self.content_ids.filtered(lambda c: c.language_code == partner_lang)
        return content.coa_body if content else ""

    def get_components_body_for_partner_lang(self, partner_lang: str) -> str:
        """Obtiene el contenido Components body adecuado basado
        en el idioma del partner."""
        self.ensure_one()
        content = self.content_ids.filtered(lambda c: c.language_code == partner_lang)
        return content.components_body if content else ""

    def get_multicolor_body_for_partner_lang(self, partner_lang: str) -> str:
        """Obtiene el contenido Multicolor body adecuado basado
        en el idioma del partner."""
        self.ensure_one()
        content = self.content_ids.filtered(lambda c: c.language_code == partner_lang)
        return content.multicolor_body if content else ""

    def get_table_batch_certificate_for_partner_lang(self, partner_lang: str) -> str:
        """Obtiene el contenido de tabla batch certificate adecuado
        basado en el idioma del partner."""
        self.ensure_one()
        content = self.content_ids.filtered(lambda c: c.language_code == partner_lang)
        return content.table_batch_certificate if content else ""
