# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError

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
    pnt_ref = fields.Char('Reference')
    pnt_partner_id = fields.Many2one(related='pnt_power_cups_id.pnt_partner_id')
    pnt_cadastral_ref = fields.Char(related='pnt_partner_id.pnt_cadastral_ref')
    pnt_dealer_id = fields.Many2one(related='pnt_power_cups_id.pnt_dealer_id')
    pnt_marketeer_id = fields.Many2one(related='pnt_power_cups_id.pnt_marketeer_id')

    pnt_kw_fw       = fields.Float(related='pnt_power_cups_id.pnt_kw_fw')
    pnt_kw_inverter = fields.Float(related='pnt_power_cups_id.pnt_kw_inverter')

    pnt_electric_type = fields.Selection(related='pnt_power_cups_id.pnt_electric_type')
    pnt_target_type = fields.Selection(related='pnt_power_cups_id.pnt_target_type')
    pnt_customer_type = fields.Selection(related='pnt_power_cups_id.pnt_customer_type')

    pnt_line_ids = fields.One2many('power.cups.shared.line', 'pnt_cups_shared_id', string='Customers')

    @api.depends('pnt_line_ids.pnt_contract_kw')
    def _get_kw_available(self):
        for record in self:
            total = 0
            for li in record.pnt_line_ids:
                total += li.pnt_contract_kw
            total = record.pnt_pnt_kw_fw - total
            record['pnt_kw_available'] = total
    pnt_kw_available = fields.Float('Available (Kw)', store=True, compute='_get_kw_available')

    @api.depends('pnt_line_ids.pnt_assigned_kw')
    def _get_kw_assigned(self):
        for record in self:
            total = 0
            for li in record.pnt_line_ids:
                total += li.pnt_assigned_kw
            record['pnt_kw_assigned'] = total
    pnt_kw_assigned = fields.Float('Assigned (Kw)', store=True, compute='_get_kw_assigned')

    """
    @api.constrains('pnt_kw_available','pnt_kw_assigned')
    def _get_constrains_kw_values(self):
        if (self.pnt_kw_available < 0) or (self.pnt_kw_assigned != self.pnt_kw_fw):
            raise UserError("Available Kw must be positive, and all available power distributed, please review.")
        else: return True
    """

class PowerCUPSSharedLine(models.Model):
    _name = 'power.cups.shared.line'
    _description = 'Power CUPS Shared Line'

    name = fields.Many2one('res.partner', string='Customer', required=True)
    pnt_contract_kw = fields.Float('Contract (kw)')
    pnt_assigned_kw = fields.Float('Assigned (kw)')
    pnt_date_begin = fields.Date('Date begin')
    pnt_date_end = fields.Date('Date end')
    pnt_subscription_id = fields.Many2one('sale.order', string='Subscription')
    pnt_cups_shared_id = fields.Many2one('power.cups.shared', string='Shared FV')
