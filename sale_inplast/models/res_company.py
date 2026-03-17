# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    pnt_pricelist_day_lock = fields.Integer(
        "Pricelist days lock", store=True, default=15
    )
    pnt_update_month_day = fields.Integer("Pricelist update day", store=True, default=1)
    pnt_exwork_delivery_mode_id = fields.Many2one(
        "delivery.carrier", string="Exwork Delivery Mode"
    )
