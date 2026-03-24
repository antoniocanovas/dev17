# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _


class MigArticuloIdioma(models.Model):
    _name = 'mig.articuloidioma'
    _description = 'MIG Articulo Idioma'

    name = fields.Char('Nombre (desc1)')
    codarticulo = fields.Char('Código Artículo')
    descripcion = fields.Char('Descripcion2')
    idioma = fields.Char('Idioma')
