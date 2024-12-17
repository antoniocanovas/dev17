from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends('partner_id')
    def _get_partner_referrers(self):
        for record in self:
            lines = []
            # Creación de líneas de comisionistas desde el partner:
            if record.partner_id.referrer_plan_ids.ids and record.id:
                for li in record.partner_id.referrer_plan_ids:
                    newline = self.env['referrer.plan.rel'].create({
                        'referrer_id': li.referrer_id.id,
                        'commission_plan_id': li.commission_plan_id.id,
                        'sale_id': record.id,
                    })
                    lines.append(newline.id)
            record['referrer_plan_ids'] = [(6,0,lines)]
    referrer_plan_ids = fields.One2many('referrer.plan.rel', 'sale_id', string='Referrers', store=True,
                                        compute='_get_partner_referrers'
                                        )

    """
    def _create_invoices(self):
        super()._create_invoices()
        for record in self:
            lines = []
            if record.referrer_plan_ids.ids:
                for li in record.referrer_plan_ids:
                    newline = self.env['referrer.plan.rel'].create({
                        'referrer_id': li.referrer_id.id,
                        'commission_plan_id': li.commission_plan_id.id,
                        'invoice_id': nuevafactura.id,
                    })
                    lines.append(newline.id)
            record['referrer_plan_ids'] = [(6,0,lines)]
    """