from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends('partner_id')
    def _get_partner_referrers(self):
        for record in self:
            lines = []
            # Comisionista por defecto la central, pero si puede tener distinto cada delegacion, toma el del partner:
            referrers = record.partner_id.commercial_partner_id.referrer_plan_ids
            if not self.env.company.customer_referrer_unique:
                referrers = record.partner_id.referrer_plan_ids

            # Creación de líneas de comisionistas desde el partner:
            if referrer.ids and record.id:
                for li in referrers:
                    newline = self.env['referrer.plan.rel'].create({
                        'referrer_id': li.referrer_id.id,
                        'commission_plan_id': li.commission_plan_id.id,
                        'sale_id': record.id,
                    })
                    # Para evitar que en la creación ponga el valor por defecto y tome el de la factura:
                    newline.write({'commission_plan_id':li.commission_plan_id.id})
                    lines.append(newline.id)
            record['referrer_plan_ids'] = [(6,0,lines)]
    referrer_plan_ids = fields.One2many('referrer.plan.rel', 'sale_id', string='Referrers', store=True,
                                        compute='_get_partner_referrers'
                                        )
    referrer_plan_view_ids = fields.One2many(related='referrer_plan_ids')
