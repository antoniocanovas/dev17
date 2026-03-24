# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _


class Migembalaje(models.Model):
    _name = 'mig.embalaje'
    _description = 'MIG embalaje'

    name = fields.Char('Embalaje (name)')
    producto = fields.Char('producto')
    cantidad = fields.Float('cantidad')
    cajapalet = fields.Char('cajapalet')
    escaja = fields.Boolean('escaja')
    bom_line_id = fields.Many2one('mrp.bom.line', string="Bom line")
    cajapaletnull = fields.Boolean('cajapaletnull', help="Nº de tapones en configuración de producto base nulo para caja o palet.")