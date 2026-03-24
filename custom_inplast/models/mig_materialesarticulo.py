# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _


class MigMaterialesArticulo(models.Model):
    _name = 'mig.materialesarticulo'
    _description = 'MIG Materiales Artículo'

    name = fields.Char('Producto')
    componente = fields.Char('Componente')
    cantidad = fields.Float('Cantidad')
    tipo = fields.Integer('Tipo Material')
    bom_line_id = fields.Many2one('mrp.bom.line', string="Bom line")