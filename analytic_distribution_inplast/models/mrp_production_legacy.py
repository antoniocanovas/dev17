# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api


class MrpProductionLegacy(models.Model):
    _name = 'mrp.production.legacy'
    _description = 'MRP Production Legacy'

    name = fields.Many2one(
        'product.template',
        string='Producto',
        required=True,
        domain="[('pnt_product_type', '=', 'packing')]",
    )
    product_qty = fields.Float(
        'Quantity',
        required=True,
    )
    parent_id = fields.Many2one(
        'product.template',
        string='Parent',
        related='name.pnt_parent_id',
    )
    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.today,
    )
    machine_plan_id = fields.Many2one(
        'account.analytic.plan',
        string='Machine Plan',
        default=lambda self: self.env.company.analytic_machine_plan_id,
    )
    machine_id = fields.Many2one(
        'account.analytic.account',
        string='Machine',
        required=True,
        options="{'no_create': True}",
        domain="[('plan_id', '=', machine_plan_id)]",
    )
    time = fields.Float(
        string='Time',
        required=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
    )

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        defaults['machine_plan_id'] = self.env.company.analytic_machine_plan_id.id
        return defaults

    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.machine_plan_id = self.company_id.analytic_machine_plan_id
