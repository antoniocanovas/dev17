from odoo import models, fields, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _get_product_exclusive_risk(self):
        for record in self:
            value = 0
            products = self.env['product.product'].search([('partner_requesting_id','=',record.id)])
            for p in products:
                if p.qty_available > 0:
                    value += p.standard_price * p.qty_available
            record['product_exclusive_risk'] = value
    product_exclusive_risk = fields.Monetary('Stock risk', help='Stock risk in exclusive products.',
                                             compute='_get_product_exclusive_risk')
