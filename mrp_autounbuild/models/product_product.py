# -*- coding: utf-8 -*-
from odoo import models, fields, _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_open_unbuild_wizard(self):
        self.ensure_one()
        return {
            'name': _('Unbuild Product'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.unbuild.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.id,
            },
        }
