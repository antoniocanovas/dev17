# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import fields, models, _, api
from odoo.exceptions import UserError
from odoo.tools import file_open


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def add_pallet_boxes(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pallet.boxes.wizard',
            'views': [[self.env.ref('mrp_inplast.view_add_pallet_boxes_wizard').id, 'form']],
            'name': _('Add Boxes'),
            'target': 'new',
            'context': {
                'production_id': self.id,
            }
        }

