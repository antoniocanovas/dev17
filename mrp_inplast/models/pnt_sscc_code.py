# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api
from odoo.exceptions import ValidationError


class PntSsccCode(models.Model):
    _name = "pnt.sscc.code"

    lot_id = fields.Many2one("stock.lot", string="Lot")
    name = fields.Char("Name")
