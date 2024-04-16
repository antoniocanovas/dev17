# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _


class MigComponentesArticulo(models.Model):
    _name = 'mig.componentes'
    _description = 'MIG Componentes'

    name = fields.Char('Producto')
    componente = fields.Char('Componente')
    cantidad = fields.Float('Cantidad')
    bom_line_id = fields.Many2one('mrp.bom.line', string="Bom line")