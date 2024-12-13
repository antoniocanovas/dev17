from odoo import _, api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    risk_batch_id = fields.Many2one(
        "risk.batch", string="Risk batch", store=True, copy=False
    )
    credit_limit = fields.Float(related="partner_id.credit_limit")

    @api.depends('commercial_partner_id.country_id')
    def _get_is_my_country(self):
        for record in self:
            is_my_country = False
            local_country = self.env.company.country_id
            if record.commercial_partner_id.country_id == local_country:
                is_my_country = True
            record['is_my_country'] = is_my_country
    is_my_country = fields.Boolean('National', help='National / export', compute='_get_is_my_country')

    is_confirming = fields.Boolean(related='payment_mode_id.is_confirming')