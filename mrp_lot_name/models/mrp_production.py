# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


import logging

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = 'mrp.production'


    def action_confirm(self):
        res = super().action_confirm()
        if (self.product_id.tracking == 'lot') and (not self.lot_producing_id.id):
            if (self.company_id.pnt_mrp_lot_name == 'mo'):
                name = self.name.split("/")[0] + self.name.split("/")[1] + self.name.split("/")[2]
                newlot = self.env['stock.lot'].create({'name': name, 'product_id': self.product_id.id})
                self.lot_producing_id = newlot.id
            # ... put here other "else" options to naming lot ...
        return True
