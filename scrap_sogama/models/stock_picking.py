# -*- coding: utf-8 -*-

from odoo import models, fields

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    kg_ferreo = fields.Float(string='Férreo (kg)', digits='Stock Weight')
    kg_no_ferreo = fields.Float(string='No férreo (kg)', digits='Stock Weight')
    kg_metal = fields.Float(string='Metales (kg)', digits='Stock Weight')
    kg_plastico = fields.Float(string='Plástico (kg)', digits='Stock Weight')
