# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    ipnr_enable = fields.Boolean(string="Enable IPNR", store=True)
    ipnr_date_from = fields.Date(
        help="IPNR can only be applied from this date.", default="2023-01-01"
    )
    ipnr_show_in_reports = fields.Boolean(
        string="Show detailed IPNR amount in report lines",
        help="If active, IPNR amount is shown in reports.",
    )

    plastic_journal_id = fields.Many2one("account.journal", string="Tax journal")
    plastic_acquirer_account_id = fields.Many2one(
        "account.account",
        string="Acquirer account",
        help="Plastic AEAT account for acquirer operations with plastic.",
    )
    plastic_manufacture_account_id = fields.Many2one(
        "account.account",
        string="Manufactured account",
        help="Plastic AEAT account for manufacturing plastics.",
    )

    company_plastic_acquirer = fields.Boolean(string="Plastic Acquirer", default=True)
    company_plastic_manufacturer = fields.Boolean(
        string="Plastic Manufacturer", default=False
    )

    auto_validate_ipnr_purchase = fields.Boolean(
        string="Validación automática apunte IPNR en compras",
        help="Si está activo, el apunte contable de IPNR en facturas de compra "
        "se validará automáticamente al confirmar la factura. Esto agiliza "
        "el proceso contable pero requiere que la configuración IPNR sea "
        "correcta.",
        default=False,
    )

    auto_validate_ipnr_sale = fields.Boolean(
        string="Validación automática apunte IPNR en ventas",
        help="Si está activo, el apunte contable de IPNR en facturas de venta "
        "se validará automáticamente al confirmar la factura. Esto agiliza "
        "el proceso contable pero requiere que la configuración IPNR sea "
        "correcta.",
        default=False,
    )

    ipnr_consolidate_lines = fields.Boolean(
        string="Consolidar líneas IPNR en facturas",
        help="Si está activo, cuando una factura se genere desde múltiples "
        "pedidos (compra o venta), todas las líneas IPNR se consolidarán "
        "en una única línea con la suma total de cantidades e importes. "
        "Esto mejora la legibilidad de la factura y simplifica el apunte "
        "contable asociado.\n\n"
        "La consolidación:\n"
        "• Suma las cantidades de todas las líneas IPNR\n"
        "• Calcula la distribución analítica ponderada\n"
        "• Mantiene la trazabilidad con los pedidos origen",
        default=True,
    )

    def _get_today_plastic_tax(self):
        price = 0
        today = datetime.today()
        line = self.env["l10n.es.ipnr.amount"].search(
            [
                ("price", ">", 0),
                ("date_from", "<=", today),
                "|",
                ("date_to", "=", False),
                ("date_to", ">=", today),
            ],
            limit=1,
        )
        if line.id:
            price = line.price
        self.plastic_tax = price

    plastic_tax = fields.Monetary("IPNR Tax", compute="_get_today_plastic_tax")

    @api.constrains("ipnr_enable", "ipnr_date_from")
    def _check_ipnr_date(self):
        if self.filtered(lambda a: a.ipnr_enable and not a.ipnr_date_from):
            raise ValidationError(
                _("'Ipnr Date From' is mandatory for companies with IPNR enabled.")
            )
