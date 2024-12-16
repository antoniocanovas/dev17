from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends('partner_id')
    def _get_partner_referrers(self):
        self.referrer_plan_ids = [(6,0,[self.partner_id.refferrer_plan_ids.ids])]
    referrer_plan_ids = fields.One2many('referrer.plan.rel', 'sale_id', string='Referrers', store=True,
                                        compute='_get_partner_referrers')
