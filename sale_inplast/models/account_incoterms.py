import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class AccountIncoterms(models.Model):
    _inherit = "account.incoterms"

    is_exwork = fields.Boolean(
        string="Is Exwork",
        help="Indicates if this incoterm is an Exwork type",
        default=False,
    )
