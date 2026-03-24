# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api


class StockLot(models.Model):
    _inherit = "stock.lot"


    # Campos de migración facilitados por el cliente, se pueden eliminar en un futuro para PROVEEDORES (de momento):
    mig_fechafabricacion = fields.Char('Fecha fabricación')
    mig_fechafinfabricacion = fields.Char('Fecha fin fabricación')
