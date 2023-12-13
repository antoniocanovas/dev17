# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api

class WpTemplate(models.Model):
    _name = 'wp.template'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'WP Template'

    name = fields.Char('name', store=True, required=True)
    active = fields.Boolean('Active', store=True, default=True)
    wp_pico = fields.Float('Watio pico', store=True, copy=True, default=0)
    wp_hour = fields.Float('Watio hora', store=True, copy=True, default=0)
    wp_margin = fields.Float('Margin', store=True, copy=True, default=0)
    wp_charger_margin = fields.Float('Charger margin', store=True, copy=True, default=0)
    line_ids = fields.One2many('wp.template.line', 'wp_template_id', string='Lines', store=True)

    @api.depends('line_ids.factor')
    def _get_factor_sumatory(self):
        total = 0
        for li in self.line_ids:
            total += li.factor
        self.factor_total = total
    factor_total = fields.Float('Factor sum', store=False, compute='_get_factor_sumatory')