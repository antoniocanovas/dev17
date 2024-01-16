from odoo import _, api, fields, models


class SaleOrderTemplate(models.Model):
    _inherit = 'sale.subscription.plan'

    create_task = fields.Selection([('draft','Draft invoice'),('posted','Posted invoice')], store=True, copy=True,
                                   string='Task creation')
