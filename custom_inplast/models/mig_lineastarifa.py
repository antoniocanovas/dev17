# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _


class MigLineasTarifa(models.Model):
    _name = 'mig.lineastarifa'
    _description = 'MIG Líneas Tarifa'

    name = fields.Char('Cadena')
    clientecod = fields.Char('clientecod')
    cliente = fields.Char('cliente')
    articulo = fields.Char('articulo')
    familia = fields.Char('familia')
    subfamilia = fields.Char('subfamilia')
    fechavalideztarifa = fields.Date('fechavalideztarifa')
    fechalimitepedido = fields.Date('fechalimitepedido')
    fechaactualizacion = fields.Date('fechaactualizacion')
    eneuros = fields.Char('eneuros')
    codigodivisa = fields.Char('codigodivisa')
    preciooferta = fields.Char('preciooferta')
    precioetileno = fields.Char('precioetileno')
    comentario = fields.Char('comentario')
    articulocodcliente = fields.Char('articulocodcliente')
    pricelist_id = fields.Many2one('product.pricelist', string="pricelist")
