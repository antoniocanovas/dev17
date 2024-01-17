

from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError


class PntCoa(models.Model):
    _name = "pnt.coa"
    _description = "COA fields"

    name = fields.Char(
        string="Name"
    )
    pnt_coa_body = fields.Html(
        string="Body"
    )
