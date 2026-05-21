# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models


class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env.company.sscc_sequence_id
        if sequence:
            for vals in vals_list:
                vals['name'] = sequence.next_by_id()
        return super().create(vals_list)
