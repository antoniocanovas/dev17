# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = "product.pricelist"


    # Campos de migración facilitados por el cliente, se pueden eliminar en un futuro para PROVEEDORES (de momento):
    mig_codigocliente = fields.Char('mig_codigocliente')
