from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError


class PntCoaContent(models.Model):
    _name = "pnt.coa.content"
    _description = "COA Content per Language"

    # Relación con el modelo PntCoa
    coa_id = fields.Many2one(
        "pnt.coa", string="COA Reference", required=True, ondelete="cascade"
    )
    language_code = fields.Char(string="Language Code", required=True)

    coa_body = fields.Binary(string="COA Body")
    multicolor_body = fields.Binary(string="Multicolor Body")
    components_body = fields.Binary(string="Components Body")
