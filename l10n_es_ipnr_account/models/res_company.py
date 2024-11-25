# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from datetime import datetime

class ResCompany(models.Model):
    _inherit = "res.company"

    ipnr_enable = fields.Boolean(compute='check_ipnr_enable', store = True)
    ipnr_date_from = fields.Date(help="IPNR can only be applied from this date.", default='2023-01-01')
    ipnr_show_in_reports = fields.Boolean(
        string="Show detailed IPNR amount in report lines",
        help="If active, IPNR amount is shown in reports.",
    )

    plastic_journal_id = fields.Many2one('account.journal', string='Tax journal')
    plastic_commercial_account_id = fields.Many2one('account.account', string='Commercial account',
                                                        help='Plastic AEAT account for commercial operations with plastic.')
    plastic_manufacture_account_id = fields.Many2one('account.account', string='Manufactured account',
                                                         help='Plastic AEAT account for manufacturing plastics.')

    company_plastic_acquirer = fields.Boolean(string="Plastic Acquirer", default=True)
    company_plastic_manufacturer = fields.Boolean(string="Plastic Manufacturer", default=False)


    def _get_today_plastic_tax(self):
        price = 0
        today = datetime.today()
        line = self.env['l10n.es.ipnr.amount'].search([
            ('price','>',0),('date_from','<=',today),'|',('date_to','=',False),('date_to','>=',today)],limit=1)
        if line.id: price = line.price
        self.plastic_tax = price
    plastic_tax = fields.Monetary('IPNR Tax', compute='_get_today_plastic_tax')

#    @api.depends('company_plastic_acquirer', 'company_plastic_manufacturer')
    @api.depends('company_plastic_acquirer', 'company_plastic_manufacturer')
    def check_ipnr_enable(self):
        for record in self:
            ipnr_enable = False
            if record.company_plastic_acquirer or record.company_plastic_manufacturer:
                ipnr_enable = True
            record.ipnr_enable = ipnr_enable

    @api.constrains("ipnr_enable", "ipnr_date_from")
    def _check_pnr_date(self):
        if self.filtered(lambda a: a.ipnr_enable and not a.ipnr_date_from):
            raise ValidationError(
                _("'Ipnr Date From' is mandatory for companies with IPNR enabled.")
            )
