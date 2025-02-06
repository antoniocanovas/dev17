# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api
from datetime import datetime
from odoo.exceptions import UserError

class AnalyticDistributionParameter(models.Model):
    _name = 'analytic.distribution.parameter'
    _description = 'Analytic distribution parameters'

    name = fields.Char('Name', required=True)
