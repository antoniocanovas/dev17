# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    default_stock_putaway_rule_id = fields.Many2one('stock.putaway.rule', string='Default stock rule')
