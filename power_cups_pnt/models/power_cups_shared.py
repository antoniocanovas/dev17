# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _


class PowerCUPSShared(models.Model):
    _name = 'power.cups.shared'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Power CUPS Shared'

    name = fields.Char('Name', store=True, copy=True, required=True)

    pnt_state = fields.Selection(
        selection=[('draft','Draft'),('proposal','Proposal'),('done','Done'),('cancel','Cancel')],
        string="State",
        default='draft',
        tracking=True,
    )

    pnt_power_cups_id = fields.Many2one('power.cups', string='CUPS', store=True, copy=False)
    pnt_partner_id = fields.Many2one(related='pnt_power_cups_id.pnt_partner_id')
    pnt_cadastral_ref = fields.Char(related='pnt_partner_id.pnt_cadastral_ref')
    pnt_dealer_id = fields.Many2one(related='pnt_power_cups_id.pnt_dealer_id')
    pnt_marketeer_id = fields.Many2one(related='pnt_power_cups_id.pnt_marketeer_id')

    pnt_kw_fw       = fields.Float(related='pnt_power_cups_id.pnt_kw_fw')
    pnt_kw_inverter = fields.Float(related='pnt_power_cups_id.pnt_kw_inverter')

    pnt_electric_type = fields.Selection(related='pnt_power_cups_id.pnt_electric_type')
    pnt_target_type = fields.Selection(related='pnt_power_cups_id.pnt_target_type')
    pnt_customer_type = fields.Selection(related='pnt_power_cups_id.pnt_customer_type')

    pnt_lines_ids = fields.One2many('power.cups.shared.line', 'cups_shared_id', string='Customers')

class PowerCUPSSharedLine(models.Model):
    _name = 'power.cups.shared.line'
    _description = 'Power CUPS Shared Line'

    name = fields.Many2one('res.partner', string='Customer', required=True)
    cups_shared_id = fields.Many2one('power.cups.shared', string='Shared FV')
