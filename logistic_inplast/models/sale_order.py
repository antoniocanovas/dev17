from odoo import _, api, fields, models

class SaleOrder(models.Model):
    _inherit = 'sale.order'


    default_container_id = fields.Many2one('container.type', related='partner_id.container_id')
    container_ids = fields.Many2many('container.type', related='partner_id.container_ids')

    @api.depends('partner_id')
    def _get_default_container_id(self):
        self.container_id = self.partner_id.container_id.id
    container_id = fields.Many2one('container.type', string='Container type', readonly=False,
                                   compute='_get_default_container_id')

    logistic1_start = fields.Date("Logistic 1 start")
    logistic1_stop = fields.Date("Logistic 1 stop")
    logistic2_start = fields.Date("Logistic 2 start")
    logistic2_stop = fields.Date("Logistic 2 stop")
    logistic3_start = fields.Date("Logistic 3 start")
    logistic3_stop = fields.Date("Logistic 3 stop")

    @api.depends(
        "logistic1_start",
        "logistic1_stop",
        "logistic2_stop",
        "logistic3_stop",
        "create_date",
    )
    def _get_logistic_days(self):
        for record in self:
            days = 0
            if not record.logistic1_start:
                continue
            if record.logistic1_stop:
                days = int((record.logistic1_stop - record.logistic1_start).days)
            if record.logistic2_stop:
                days = int((record.logistic2_stop - record.logistic1_start).days)
            if record.logistic3_stop:
                days = int((record.logistic3_stop - record.logistic1_start).days)
            record["logistic_days"] = days
            for line in record.order_line:
                line.customer_lead = days

    logistic_days = fields.Integer("Days", store=True, compute="_get_logistic_days")
