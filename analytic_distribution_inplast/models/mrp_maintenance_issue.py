# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api


class MrpMaintenanceIssue(models.Model):
    _name = 'mrp.maintenance.issue'
    _description = 'Maintenance Issue'

    name = fields.Char(
        string='Name',
        default='/',
        store=True,
    )
    date = fields.Date(
        string='Date',
        default=fields.Date.today,
        required=True,
    )
    machine_id = fields.Many2one(
        'account.analytic.account',
        string='Machine',
        required=True,
        options="{'no_create': True}",
        domain="[('plan_id', '=', machine_plan_id)]",
    )
    machine_plan_id = fields.Many2one(
        'account.analytic.plan',
        string='Machine Plan',
    )
    department_id = fields.Many2one(
        'account.analytic.account',
        string='Department',
        required=True,
        options="{'no_create': True}",
        domain="[('id', 'in', [workshop_department_id, maintenance_department_id])]",
    )
    department_plan_id = fields.Many2one(
        'account.analytic.plan',
        string='Department Plan',
    )
    workshop_department_id = fields.Many2one(
        'account.analytic.account',
        string='Workshop Department',
    )
    maintenance_department_id = fields.Many2one(
        'account.analytic.account',
        string='Maintenance Department',
    )
    time = fields.Float(
        string='Time',
        required=True,
        help='Maintenance downtime duration (hours and minutes).',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
    )

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        company = self.env.company
        defaults['machine_plan_id'] = company.analytic_machine_plan_id.id
        defaults['department_plan_id'] = company.analytic_department_plan_id.id
        defaults['workshop_department_id'] = company.analytic_workshop_department_id.id
        defaults['maintenance_department_id'] = company.analytic_maintenance_department_id.id
        return defaults

    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.machine_plan_id = self.company_id.analytic_machine_plan_id
        self.department_plan_id = self.company_id.analytic_department_plan_id
        self.workshop_department_id = self.company_id.analytic_workshop_department_id
        self.maintenance_department_id = self.company_id.analytic_maintenance_department_id
