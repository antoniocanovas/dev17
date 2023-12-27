# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api


class ProductBrand(models.Model):
    _inherit = "res.partner"

    # Para borrar después de la migración:
    mig_agente_pnt = fields.Char(string='mig_agente_pnt', store=True)
    mig_agente2_pnt = fields.Char(string='mig_agente2_pnt', store=True)
    mig_nif_pnt = fields.Char(string='mig_nif_pnt', store=True)
    mig_banco_pnt = fields.Char(string='mig_banco_pnt', store=True)
    mig_iban_pnt = fields.Char(string='mig_iban_pnt', store=True)
    mig_exportacion_pnt = fields.Char(string='mig_exportacion_pnt', store=True)
