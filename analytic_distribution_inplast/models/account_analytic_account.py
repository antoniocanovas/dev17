# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api

class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    _sql_constraints = [
        ('workcenter_id_unique', 'UNIQUE(workcenter_id)', 'Este centro de trabajo ya está asignado a otra cuenta analítica.'),
    ]

    product_id = fields.Many2one('product.product', string='Distribution Product')
    workcenter_id = fields.Many2one('mrp.workcenter', string='Workcenter')
    is_machine_plan = fields.Boolean(compute='_compute_is_machine_plan')

    @api.depends('plan_id', 'company_id', 'company_id.analytic_machine_plan_id')
    def _compute_is_machine_plan(self):
        for record in self:
            record.is_machine_plan = bool(
                record.plan_id
                and record.company_id.analytic_machine_plan_id
                and record.plan_id == record.company_id.analytic_machine_plan_id
            )
