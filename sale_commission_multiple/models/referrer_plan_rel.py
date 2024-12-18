from odoo import _, api, fields, models


class ReferrerPlanRel(models.Model):
    _name = "referrer.plan.rel"
    _description = "Referrer plan relation"

    name = fields.Char("Name", compute='_get_name')
    commission_plan_id = fields.Many2one("commission.plan", string="Commission Plan", store=True,
                                         compute="_get_default_commission_plan_id")
    partner_id = fields.Many2one('res.partner', string="Customer")
    referrer_id = fields.Many2one('res.partner', string="Referrer")
    # Campos de relación para o2m:
    sale_id = fields.Many2one('sale.order', string="Sale order")
    invoice_id = fields.Many2one('account.move', string="Invoice")
    # Registro de comisión creada (único por factura y comisionista):
    commission_po_line_id = fields.Many2one('purchase.order.line', string="Purchase line")
    credit_commission_po_line_id = fields.Many2one('purchase.order.line', string="Purchase credit")

    @api.depends('partner_id','referrer_id')
    def _get_name(self):
        for record in self:
            name = ""
            if record.referrer_id.id:
                name += record.referrer_id.name
            if record.commission_plan_id.id:
                name += " (" + record.commission_plan_id.name + ")"
            record['name'] = name

    @api.depends('referrer_id')
    def _get_default_commission_plan_id(self):
        for record in self:
            record['commission_plan_id'] = record.referrer_id.commission_plan_id.id

