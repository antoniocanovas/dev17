from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError

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
    print_multicolor = fields.Boolean("Multicolor print")
    print_quality_meassure = fields.Boolean("Quality meassures")
    print_components = fields.Boolean("Components print")

    material_number = fields.Char("Material Number")
    specification_number = fields.Char("Specifitacion Number")
    vendor_site_number = fields.Char("Vendor Site Number")

    language_selection = fields.Selection(
        selection="_get_available_languages",
        string="Select Language",
        default=lambda self: self.env.lang,
    )

    content_ids = fields.One2many("pnt.coa.content", "coa_id", string="COA Contents")

    selected_coa_body = fields.Html(
        string="Selected COA Body", compute="_compute_selected_coa_body", store=True
    )
    selected_multicolor_body = fields.Html(
        string="Selected Multicolor Body",
        compute="_compute_selected_multicolor_body",
        store=True,
    )
    selected_components_body = fields.Html(
        string="Selected Components Body",
        compute="_compute_selected_components_body",
        store=True,
    )

    def _get_available_languages(self):
        """Obtiene los idiomas configurados en Odoo y los devuelve como opciones para selección."""
        languages = self.env["res.lang"].search([("active", "=", True)])
        return [(lang.code, lang.name) for lang in languages]

    @api.depends("language_selection", "content_ids")
    def _compute_selected_coa_body(self):
        """Calcula qué cuerpo de COA mostrar en función del idioma seleccionado."""
        for record in self:
            content = record.content_ids.filtered(
                lambda c: c.language_code == record.language_selection
            )
            record.selected_coa_body = content.coa_body if content else ""

    @api.depends("language_selection", "print_multicolor", "content_ids")
    def _compute_selected_multicolor_body(self):
        """Calcula qué tabla multicolor mostrar en función del idioma seleccionado."""
        for record in self:
            content = record.content_ids.filtered(
                lambda c: c.language_code == record.language_selection
            )
            record.selected_multicolor_body = (
                content.multicolor_body if content and record.print_multicolor else ""
            )

    @api.depends("language_selection", "print_components", "content_ids")
    def _compute_selected_components_body(self):
        """Calcula qué tabla de componentes mostrar en función del idioma seleccionado."""
        for record in self:
            content = record.content_ids.filtered(
                lambda c: c.language_code == record.language_selection
            )
            record.selected_components_body = (
                content.components_body if content and record.print_components else ""
            )

    def create(self, vals):
        """Crea automáticamente registros de contenido COA para cada idioma configurado."""
        # Crea el registro principal de COA
        coa_record = super(PntCoa, self).create(vals)

        # Obtiene todos los idiomas activos en Odoo
        active_languages = self.env["res.lang"].search([("active", "=", True)])

        # Crea un registro de contenido por cada idioma
        for lang in active_languages:
            self.env["pnt.coa.content"].create(
                {
                    "coa_id": coa_record.id,
                    "language_code": lang.code,
                    "coa_body": "",  # Puedes personalizar el contenido predeterminado
                    "multicolor_body": "",
                    "components_body": "",
                }
            )

        return coa_record

    def get_coa_body_for_partner_lang(self, partner_lang):
        """Obtiene el contenido COA body adecuado basado en el idioma del partner."""
        self.ensure_one()
        content = self.content_ids.filtered(lambda c: c.language_code == partner_lang)
        return content.coa_body if content else ""

    def get_components_body_for_partner_lang(self, partner_lang):
        """Obtiene el contenido Components body adecuado basado en el idioma del partner."""
        self.ensure_one()
        content = self.content_ids.filtered(lambda c: c.language_code == partner_lang)
        return content.components_body if content else ""

    def get_multicolor_body_for_partner_lang(self, partner_lang):
        """Obtiene el contenido Multicolor body adecuado basado en el idioma del partner."""
        self.ensure_one()
        content = self.content_ids.filtered(lambda c: c.language_code == partner_lang)
        return content.multicolor_body if content else ""

    def write(self, vals):
        res = super(PntCoa, self).write(vals)
        if "language_selection" in vals:
            self._compute_selected_components_body()
        return res
