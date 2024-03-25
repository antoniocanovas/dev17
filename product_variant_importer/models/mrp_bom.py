# Copyright Serincloud SL - Ingenieriacloud.com


from odoo import fields, models, api

class MrpBom(models.Model):
    _inherit = "mrp.bom"

    # Pares por variante de producto, se usará en el cálculo de tarifas y líneas de venta:
    @api.depends('bom_line_ids','bom_line_ids.product_qty')
    def _get_shoes_bom_pair_count(self):
        for record in self:
            count = 0
            if record.bom_line_ids.ids:
                for li in record.bom_line_ids:
                    count += li.product_qty
            else: count = 1
            record['pairs_count'] = count
    pairs_count = fields.Integer('Pairs', store=True, compute='_get_shoes_bom_pair_count')

