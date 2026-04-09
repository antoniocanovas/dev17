# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    analytic_product_plan_id = fields.Many2one('account.analytic.plan', string='Product plan')
    analytic_fixed_variable_plan_id = fields.Many2one('account.analytic.plan', string='Fixed/variable plan')
    analytic_machine_plan_id = fields.Many2one('account.analytic.plan', string='Machines plan')
    analytic_equipment_plan_id = fields.Many2one('account.analytic.plan', string='Equipment plan')
    analytic_department_plan_id = fields.Many2one('account.analytic.plan', string='Department plan')

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Buscar campos que se crean dinámicamente en account.analytic.line con cada plan, son del tipo "x_":
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    product_field_id = fields.Many2one(
        'ir.model.fields', string='Product field',
        store=True, compute='_get_product_field'
    )
    fixed_variable_field_id = fields.Many2one(
        'ir.model.fields', string='Fixed/variable field',
        store=True, compute='_get_fixed_variable_field'
    )
    machine_field_id = fields.Many2one(
        'ir.model.fields', string='Machines field',
        store=True, compute='_get_machine_field'
    )
    equipment_field_id = fields.Many2one(
        'ir.model.fields', string='Equipment field',
        store=True, compute='_get_equipment_field'
    )
    department_field_id = fields.Many2one(
        'ir.model.fields', string='Department field',
        store=True, compute='_get_department_field'
    )

    @api.depends('analytic_product_plan_id')
    def _get_product_field(self):
        standard_plan_id = self.env.ref('analytic.analytic_plan_projects')
        if self.analytic_product_plan_id == standard_plan_id:
            aal_field = self.env.ref('analytic.field_account_analytic_line__account_id')
        else:
            aal_field = self.env['ir.model.fields'].search([
                ('model', '=', 'account.analytic.line'),
                ('ttype', '=', 'many2one'),
                ('field_description', '=', self.analytic_product_plan_id.name),
            ])
        self.product_field_id = aal_field

    @api.depends('analytic_fixed_variable_plan_id')
    def _get_fixed_variable_field(self):
        standard_plan_id = self.env.ref('analytic.analytic_plan_projects')
        if self.analytic_fixed_variable_plan_id == standard_plan_id:
            aal_field = self.env.ref('analytic.field_account_analytic_line__account_id')
        else:
            aal_field = self.env['ir.model.fields'].search([
                ('model', '=', 'account.analytic.line'),
                ('ttype', '=', 'many2one'),
                ('field_description', '=', self.analytic_fixed_variable_plan_id.name),
            ])
        self.fixed_variable_field_id = aal_field


    @api.depends('analytic_machine_plan_id')
    def _get_machine_field(self):
        standard_plan_id = self.env.ref('analytic.analytic_plan_projects')
        if self.analytic_machine_plan_id == standard_plan_id:
            aal_field = self.env.ref('analytic.field_account_analytic_line__account_id')
        else:
            aal_field = self.env['ir.model.fields'].search([
                ('model', '=', 'account.analytic.line'),
                ('ttype', '=', 'many2one'),
                ('field_description', '=', self.analytic_machine_plan_id.name),
            ])
        self.machine_field_id = aal_field

    @api.depends('analytic_equipment_plan_id')
    def _get_equipment_field(self):
        standard_plan_id = self.env.ref('analytic.analytic_plan_projects')
        if self.analytic_equipment_plan_id == standard_plan_id:
            aal_field = self.env.ref('analytic.field_account_analytic_line__account_id')
        else:
            aal_field = self.env['ir.model.fields'].search([
                ('model', '=', 'account.analytic.line'),
                ('ttype', '=', 'many2one'),
                ('field_description', '=', self.analytic_equipment_plan_id.name),
            ])
        self.equipment_field_id = aal_field

    @api.depends('analytic_department_plan_id')
    def _get_department_field(self):
        standard_plan_id = self.env.ref('analytic.analytic_plan_projects')
        if self.analytic_department_plan_id == standard_plan_id:
            aal_field = self.env.ref('analytic.field_account_analytic_line__account_id')
        else:
            aal_field = self.env['ir.model.fields'].search([
                ('model', '=', 'account.analytic.line'),
                ('ttype', '=', 'many2one'),
                ('field_description', '=', self.analytic_department_plan_id.name),
            ])
        self.department_field_id = aal_field


    analytic_fixed_account_id = fields.Many2one('account.analytic.account', string='Fixed expense')
    analytic_variable_account_id = fields.Many2one('account.analytic.account', string='Variable expense')
    mrp_workcenter_tag_ids = fields.Many2many(
        'mrp.workcenter.tag', string='Machine groups',
        help='Grupos de máquinas utilizados en las distribuciones analíticas'
    )

    analytic_warehouse_department_id = fields.Many2one('account.analytic.account', string='Warehouse')
    analytic_maintenance_department_id = fields.Many2one('account.analytic.account', string='Maintenance')
    analytic_sale_department_id = fields.Many2one('account.analytic.account', string='Sales')
    analytic_administration_department_id = fields.Many2one('account.analytic.account', string='Administration')
    analytic_quality_department_id = fields.Many2one('account.analytic.account', string='Quality')
    analytic_mrp_department_id = fields.Many2one('account.analytic.account', string='Manufacturing')
    analytic_workshop_department_id = fields.Many2one('account.analytic.account', string='Workshop')