res_partner.pyfrom odoo import models, fields


class SaleOrder(models.Model):
    _inherit = "sale.order"

    referrer_plan_ids = fields.One2many('referrer.plan.rel', 'sale_id', string='Referrers')
