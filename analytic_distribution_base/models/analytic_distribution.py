# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api
from datetime import datetime
from odoo.exceptions import UserError

class AnalyticDistribution(models.Model):
    _name = 'analytic.distribution'
    _description = 'Analytic distribution'
    _inherit = ["mail.thread", "mail.activity.mixin"]


    name = fields.Char('Name', required=True)
    date_from = fields.Date('From date', copy=False)
    date_to = fields.Date('To date', copy=False, default=lambda self: datetime.today())
    analytic_line_ids = fields.One2many('account.analytic.line', 'analytic_distribution_id', string='Analytic lines')
    comment = fields.Html('Comments', store=True, copy=False)
    line_ids = fields.One2many('analytic.distribution.line','distribution_id', string='Lines')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    days = fields.Integer('Days', compute='_compute_days', store=True)
    @api.depends('date_from','date_to')
    def _compute_days(self):
        for record in self:
            if record.date_from and record.date_to:
                record.days = (record.date_to - record.date_from).days + 1
            else:
                record.days = 0

    # Quitado porque pasamos a utilizar líneas con balance:
    #analytic_distribution_template_ids = fields.Many2many('analytic.distribution.template', string='Distributions')
    def _get_analytic_line_count(self):
        self.analytic_line_count = len(self.analytic_line_ids.ids)
    analytic_line_count = fields.Integer('Lines', compute='_get_analytic_line_count')

    def compute_distribution(self):
        for record in self:
            for li in record.line_ids:
                # Añadir aquí el borrado de apuntes analíticos anteriores.
                li.compute_debit_credit()
