from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    pnt_power_cups_id = fields.Many2one('power.cups', string='CUPS', store=True, copy=False)
    pnt_cadastral_ref = fields.Char('Cadastral ref', store=True, copy=False, tracking=True)
    pnt_partner_id = fields.Many2one('res.partner', string='Delivery address', store=False, related='pnt_power_cups_id.pnt_partner_id')
    pnt_dealer_id = fields.Many2one(
        'res.partner', string='Dealer', store=False, readonly=False, related='pnt_power_cups_id.pnt_dealer_id')
    pnt_marketeer_id = fields.Many2one(
        'res.partner', string='Marketeer', store=False, readonly=False,related='pnt_power_cups_id.pnt_marketeer_id')
    pnt_state = fields.Selection(string='CUPS State', related='pnt_power_cups_id.pnt_state', store=False)

    pnt_kw_fw       = fields.Float('Panels (kWp)', store=True, readonly=False, related='pnt_power_cups_id.pnt_kw_fw')
    pnt_kw_inverter = fields.Float('Inverter (kWn)', store=True, readonly=False, related='pnt_power_cups_id.pnt_kw_inverter')
    pnt_kw_battery  = fields.Float('Battery (kWh)', store=True, readonly=False, related='pnt_power_cups_id.pnt_kw_battery')
    pnt_kw_prve     = fields.Float('PRVE (kW)', store=True, readonly=False, related='pnt_power_cups_id.pnt_kw_prve')
    pnt_isolated    = fields.Boolean('Isolated', store=True, readonly=False, related='pnt_power_cups_id.pnt_isolated')

    pnt_electric_type = fields.Selection(
        string="Electricity",
        store=True, readonly=False,
        related='pnt_power_cups_id.pnt_electric_type',
    )

    pnt_target_type = fields.Selection(
        string="Customer type",
        store=True, readonly=False,
        related='pnt_power_cups_id.pnt_target_type',
    )

    pnt_customer_type = fields.Selection(
        string="Installation type",
        store=True, readonly=False,
        related='pnt_power_cups_id.pnt_customer_type',
    )

    pnt_rustic = fields.Boolean(
        'Rustic floor', store=True, copy=True, readonly=False, tracking=True,
        related='pnt_power_cups_id.pnt_rustic',
    )

    def _get_child_cups_count(self):
        for record in self:
            record['pnt_child_cups_count'] = self.env['power.cups'].\
                search_count(['|',('pnt_customer_id', '=', record.id),('pnt_partner_id', '=', record.id)])
    pnt_child_cups_count = fields.Integer('All CUPS', store=False, compute='_get_child_cups_count')