from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    referrer_plan_ids = fields.One2many('referrer.plan.rel', 'partner_id', string='Referrers')
