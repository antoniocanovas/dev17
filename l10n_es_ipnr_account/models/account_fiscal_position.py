# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    ipnr_subject = fields.Boolean(
        string="Subject to IPNR",
        help="If marked, this fiscal position will be considered subject to IPNR.",
    )
