from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    referrer_plan_ids = fields.One2many('referrer.plan.rel', 'partner_id', string='Referrers')
    customer_referrer_unique = fields.Boolean('Referrer unique', compute='_get_customer_referrer_unique')

    def _get_customer_referrer_unique(self):
        self.customer_referrer_unique = self.env.company.customer_referrer_unique