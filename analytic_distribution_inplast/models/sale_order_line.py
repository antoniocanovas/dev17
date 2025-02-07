# -*- coding: utf-8 -*-
# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    bom_template_type = fields.Selection(
        string="Tipo de BOM Template",
        related="product_id.bom_ids.mrp_bom_template_id.type",  # Asegúrate de que este camino es correcto
        store=True
    )


