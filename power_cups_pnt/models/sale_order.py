from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    pnt_power_cups_id = fields.Many2one('power.cups', string='CRM CUPS', store=True,
                                        related='opportunity_id.pnt_power_cups_id')
