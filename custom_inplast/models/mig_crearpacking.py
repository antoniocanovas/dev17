# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _


class MigCrearpacking(models.Model):
    _name = 'mig.crearpacking'
    _description = 'MIG Crear packings'

    # Campos de importación:
    name = fields.Char('Producto')
    mrp_type = fields.Char('mrp_type')
    sufix = fields.Char('sufix')
    box_base_qty = fields.Integer('box_base_qty')
    pallet_base_qty = fields.Float('pallet_base_qty')
    box_qty = fields.Integer('box_qty')
    # Campos de control:
    newpacking_id = fields.Many2one('product.template', string="newpacking_id")
