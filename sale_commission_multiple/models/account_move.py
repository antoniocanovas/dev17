from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = "account.move"


    @api.depends('partner_id')
    def _get_partner_referrers(self):
        for record in self:
            lines = []
            if record.partner_id.referrer_plan_ids.ids and record.id:
                for li in record.partner_id.referrer_plan_ids:
                    newline = self.env['referrer.plan.rel'].create({
                        'referrer_id': li.referrer_id.id,
                        'commission_plan_id': li.commission_plan_id.id,
                        'invoice_id': record.id,
                    })
                    lines.append(newline.id)
            record['referrer_plan_ids'] = [(6,0,lines)]
    referrer_plan_ids = fields.One2many('referrer.plan.rel', 'invoice_id', string='Referrers', store=True,
                                        compute='_get_partner_referrers')