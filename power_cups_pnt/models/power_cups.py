# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _


class PowerCUPS(models.Model):
    _name = 'power.cups'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Power CUPS'

    name = fields.Char('Name', store=True, copy=True, required=True)

    pnt_state = fields.Selection(
        selection=[('draft','Draft'),('done','Done')],
        string="State",
        default='draft',
        tracking=True,
    )

    pnt_partner_id = fields.Many2one('res.partner', string='Delivery address', store=True, copy=True, tracking=True)
    pnt_cadastral_ref = fields.Char('Cadastral ref', store=True, tracking=True, readonly=False, related='pnt_partner_id.pnt_cadastral_ref')
    pnt_dealer_id = fields.Many2one('res.partner', string='Dealer', store=True, copy=True, tracking=True)
    pnt_marketeer_id = fields.Many2one('res.partner', string='Marketeer', store=True, copy=True, tracking=True)

    @api.depends('pnt_partner_id','pnt_partner_id.parent_id')
    def _get_cups_customer(self):
        for record in self:
            customer = record.pnt_partner_id
            if customer.parent_id.id:
                customer = customer.parent_id
            record['pnt_customer_id'] = customer.id
    pnt_customer_id = fields.Many2one('res.partner', string='Customer', store=True, compute='_get_cups_customer')

    pnt_kw_fw       = fields.Float('Panels (kWp)', store=True, copy=True, tracking=True)
    pnt_kw_inverter = fields.Float('Inverter (kWn)', store=True, copy=True, tracking=True)
    pnt_kw_battery  = fields.Float('Battery (kWh)', store=True, copy=True, tracking=True)
    pnt_kw_contract = fields.Float('Contract Power (W)', store=True, copy=True, tracking=True)
    pnt_kw_access   = fields.Float('Access power (W)', store=True, copy=True, tracking=True)
    pnt_kw_prve     = fields.Float('PRVE (kW)', store=True, copy=True, tracking=True)
    pnt_isolated    = fields.Boolean('Isolated', store=True, copy=True, tracking=True)
    pnt_rustic = fields.Boolean('Rustic floor', store=True, copy=True, tracking=True, default=False)

    pnt_electric_type = fields.Selection(
        selection=[('mono','Monofásica'),
                   ('tri','Trifásica')],
        string="Power type",
        default='mono',
        store=True, copy=True,
        tracking=True,
    )

    pnt_target_type = fields.Selection(
        selection=[('acc','Autoconsumo con compensación'),
                   ('asc','Autoconsumo sin compensación'),
                   ('venta','Venta a red')],
        string="Consumption type",
        default='asc',
        store=True, copy=True,
        tracking=True,
    )

    pnt_customer_type = fields.Selection(
        selection=[('residential','Residential'),
                   ('company','Company'),
                   ('community','Shared residential'),
                   ('shared','Shared industry'),
                   ('demesol', 'Shared Demesol'),
                   ('sale', 'Energy sale'),
                   ('prve', 'PRVE'),
                   ('cee', 'CEE'),
                   ],
        string="Installation type",
        default='residential',
        store=True, copy=True,
        tracking=True,
    )
