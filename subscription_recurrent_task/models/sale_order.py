from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    subscription_project_id = fields.Many2one('project.project', string='Project',store=True, copy=True,
                                              help='In this project a new task will be created for each invoice.')
    create_task = fields.Selection(store=False, related='plan_id.create_task')