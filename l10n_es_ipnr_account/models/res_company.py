# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    ipnr_enable = fields.Boolean(compute='check_ipnr_enable', store = True)
    ipnr_date_from = fields.Date(help="IPNR can only be applied from this date.", default='2023-01-01')
    ipnr_show_in_reports = fields.Boolean(
        string="Show detailed IPNR amount in report lines",
        help="If active, IPNR amount is shown in reports.",
    )

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
