# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api


class ProductCategory(models.Model):
    _inherit = "product.category"


    # Campos de migración facilitados por el cliente, se pueden eliminar en un futuro:
    mig_cod_familia = fields.Char('mig_cod_familia')
    mig_cod_subfamilia = fields.Char('mig_cod_subfamilia')
    mig_serie = fields.Char('mig_serie')
    mig_cod_serie = fields.Char('mig_cod_serie')
    mig_serie_descripcion = fields.Char('mig_serie_descripcion')
    mig_cod_arancelario = fields.Char('mig_cod_arancelario')
    mig_grupo_iva = fields.Char('mig_grupo_iva')
    mig_ud_compra = fields.Char('mig_ud_compra')
    mig_ud_venta = fields.Char('mig_ud_venta')
    mig_fabricado_comprado = fields.Char('mig_fabricado_comprado')
    mig_cc_ventas = fields.Char('mig_cc_ventas')
    mig_precio_stock = fields.Char('mig_precio_stock')
    mig_diametro = fields.Char('mig_diametro')
    mig_cod_grupo = fields.Char('mig_cod_grupo')
    mig_cod_grupo3 = fields.Char('mig_cod_grupo3')
    mig_des_cds = fields.Char('mig_des_cds')
    mig_cod_grupo4 = fields.Char('mig_cod_grupo4')
    mig_grupo_caps = fields.Char('mig_grupo_caps')
    mig_tipoo = fields.Char('mig_tipoo')
    mig_tipopi = fields.Char('mig_tipopi')
    mig_dd = fields.Char('mig_dd')
