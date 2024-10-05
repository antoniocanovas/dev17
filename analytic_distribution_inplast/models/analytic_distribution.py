# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api
from datetime import datetime
from odoo.exceptions import UserError

class AnalyticDistribution(models.Model):
    _inherit = 'analytic.distribution'

    compute_mode = fields.Selection([('demo','demo INPLAST')])
    workcenter_ids = fields.Many2many('mrp.workcenter', string="Workcenters")

    def compute_distribution(self):
        """ Extend this function with custom Inplast analytic compute modes
        """
        super().compute_distribution()
        self.inplast_computed_modes()

    def inplast_computed_modes(self):
        raise UserError('ok')
