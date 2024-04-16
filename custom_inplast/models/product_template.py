# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = "product.template"


    # Campos de migración facilitados por el cliente, se pueden eliminar en un futuro:
    mig_necesidad_compra = fields.Char('mig_necesidad_compra')
    mig_stock_seguridad = fields.Char('mig_stock_seguridad')
    mig_criterio_compra = fields.Char('mig_criterio_compra')
    mig_compras_poq = fields.Char('mig_compras_poq')
    mig_tipo_producto = fields.Integer('mig_tipo_producto')
    mig_unidad_logistica = fields.Integer('mig_unidad_logistica')
    mig_tipo_embalaje = fields.Float('mig_tipo_embalaje')
    mig_peso_embalaje = fields.Float('mig_peso_embalaje')

    mig_cod_familia = fields.Char('mig_cod_familia')
    mig_cod_subfamilia = fields.Char('mig_cod_subfamilia')
    mig_cod_serie = fields.Char('mig_cod_serie')

    mig_almacen = fields.Char('mig_almacen')
    mig_zona_almacen = fields.Char('mig_zona_almacen')
    mig_dye = fields.Char('mig_dye')
    mig_descripcionlinea = fields.Text('mig_descripcionlinea')
    mig_comentario_articulo = fields.Text('mig_comentario_articulo')
    mig_marca_producto = fields.Char('mig_marca_producto')
    mig_barcode = fields.Char('mig_barcode')
    mig_cod_alternativo = fields.Char('mig_cod_alternativo')
    mig_cod_arancelario = fields.Char('mig_cod_arancelario')
    mig_cod_proveedor = fields.Char('mig_cod_proveedor')
    mig_material_servicio = fields.Char('mig_material_servicio')
    mig_fecha_alta = fields.Date('mig_fecha_alta')
    mig_codigo_proyecto = fields.Char('mig_codigo_proyecto')
    mig_codigo_definicion = fields.Char('mig_codigo_definicion')
    mig_iva_ventas = fields.Integer('mig_iva_ventas')
    mig_iva_compras = fields.Integer('mig_iva_compras')
    mig_peso_bruto_gr = fields.Char('mig_peso_bruto_gr')
    mig_peso_neto_gr = fields.Float('mig_peso_neto_gr')
    mig_grupo_analitico = fields.Integer('mig_grupo_analitico')
    mig_ud_palet = fields.Integer('mig_ud_palet')
    mig_tipo_coa = fields.Char('mig_tipo_coa')
    mig_nivel_compuesto = fields.Char('mig_nivel_compuesto')
    mig_obsoleto_lc = fields.Char('mig_obsoleto_lc')
    mig_obsoleto = fields.Char('mig_obsoleto')

    mig_unidades_palet = fields.Integer('mig_unidades_palet')
    mig_unidades_caja = fields.Integer('mig_unidades_caja')
    mig_etiqueta_esp_cliente = fields.Char('mig_etiqueta_esp_cliente')
