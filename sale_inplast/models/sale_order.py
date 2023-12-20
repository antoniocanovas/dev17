from odoo import _, api, fields, models
from datetime import timedelta, date
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

#    @api.onchange('partner_id', 'state')
#    def _avoid_outdated_pricelists(self):
#        today = date.today()
#        locking_days = self.env.user.company_id.pnt_pricelist_day_lock
#        lock_date = today - timedelta(days = locking_days)
#        pricelist_date = self.partner_id.property_product_pricelist.pnt_tracking_date
#        if not (pricelist_date) or (pricelist_date < lock_date):
#            raise UserError('Outdate pricelist !!')
#        return True