from odoo import _, api, fields, models


class ReferrerPlanRel(models.Model):
    _name = "referrer.plan.rel"
    _description = "Referrer plan relation"

    name = fields.Char("Name", compute='_get_name')
    commission_plan_id = fields.Many2one("commission.plan", string="Commission Plan", store=True,
                                         compute="_get_default_commission_plan_id")
    partner_id = fields.Many2one('res.partner', string="Customer")
    referrer_id = fields.Many2one('res.partner', string="Referrer")
    sale_id = fields.Many2one('sale.order', string="Sale order")
    invoice_id = fields.Many2one('account.move', string="Invoice")

    @api.depends('partner_id','referrer_id')
    def _get_name(self):
        for record in self:
            name = ""
            if record.partner_id.id:
                name += record.partner_id.name
            if record.referrer_id.id:
                name += " => " + record.referrer_id.name
            record['name'] = name

    @api.depends('referrer_id')
    def _get_default_commission_plan_id(self):
        for record in self:
            record['commission_plan_id'] = record.referrer_id.commission_plan_id.id
