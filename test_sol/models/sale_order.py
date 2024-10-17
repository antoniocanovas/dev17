# Copyright 2024 Antonio Cánovas <acanovas@puntsistemes.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order"]

    logistic1_start = fields.Date('Logistic 1 start')
    logistic1_stop = fields.Date('Logistic 1 stop')
    logistic2_start = fields.Date('Logistic 2 start')
    logistic2_stop = fields.Date('Logistic 2 stop')
    logistic3_start = fields.Date('Logistic 3 start')
    logistic3_stop = fields.Date('Logistic 3 stop')

    @api.depends('logistic1_start', 'logistic1_stop', 'logistic2_stop', 'logistic3_stop')
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
            record['logistic_days'] = days
    logistic_days = fields.Integer('Days', store=True, compute='_get_logistic_days')
