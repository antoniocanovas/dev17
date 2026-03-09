import logging
from typing import Any

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "ipnr.mixin"]

    _ipnr_secondary_unit_fields = {
        "line_ids": "invoice_line_ids",
        "date_field": "invoice_date",
        "editable_states": [
            "draft",
        ],
    }

    is_ipnr = fields.Boolean(
        string="Is IPNR",
        compute="_compute_is_ipnr",
        store=False,
    )

    @api.depends("invoice_line_ids.is_ipnr")
    def _compute_is_ipnr(self):
        for rec in self:
            rec.is_ipnr = any(line.is_ipnr for line in rec.invoice_line_ids)

    @api.depends("is_ipnr", "invoice_date", "company_id")
    def _compute_ipnr_is_date(self):
        ret = super()._compute_ipnr_is_date()
        for rec in self.filtered(
            lambda a: a.is_ipnr and not a.invoice_date and a.company_id.ipnr_date_from
        ):
            rec.ipnr_is_date = rec.create_date.date() >= rec.company_id.ipnr_date_from
        return ret

    @api.depends("invoice_line_ids")
    def _compute_ipnr_has_line(self):
        return super()._compute_ipnr_has_line()

    @api.depends("company_id")
    def _compute_ipnr_company(self):
        return super()._compute_ipnr_company()

    def ipnr_default_date(self, lines: object) -> Any:
        self.ensure_one()
        return self.invoice_date or self.create_date.date()

    def apply_ipnr(self):
        if self.env.context.get("avoid_recursion"):
            return
        ctx = {**self.env.context, "avoid_recursion": True}
        for move in self:
            move.with_context(ctx)._delete_ipnr()
            lines_to_process = move.invoice_line_ids.filtered("is_ipnr")
            for line in lines_to_process:
                ipnr_vals = move._get_ipnr_line_vals(line)
                if ipnr_vals.get("quantity", 0) > 0:
                    self.env["account.move.line"].with_context(ctx).create(ipnr_vals)

    def write(self, vals: object) -> Any:
        res = super().write(vals)
        if "invoice_line_ids" in vals or "partner_shipping_id" in vals:
            for move in self.filtered(lambda m: m.state == "draft"):
                move.apply_ipnr()
        return res

    @api.model_create_multi
    def create(self, vals_list: object) -> Any:
        moves = super().create(vals_list)
        for move in moves.filtered(lambda m: m.state == "draft"):
            move.apply_ipnr()
        return moves

    # DESARROLLO ANTONIO CÁNOVAS PARA CREAR APUNTES
    @api.depends("partner_id", "partner_shipping_id")
    def _get_picking_partner(self):
        for record in self:
            destination = record.partner_id
            if (record.move_type in ["out_invoice", "out_refund"]) and (
                record.partner_shipping_id.id
            ):
                destination = record.partner_shipping_id
            if record.move_type in ["in_invoice", "in_refund"]:
                destination = record.env.company.partner_id
            record.picking_partner_id = destination.id

    picking_partner_id = fields.Many2one(
        "res.partner",
        string="Picking destination",
        store=True,
        index=True,
        compute="_get_picking_partner",
    )

    plastictax_move_id = fields.Many2one(
        "account.move",
        store=True,
        string="Plastic tax entry",
        copy=False,
        help="El impuesto al plástico graba la introducción o fabricación del mismo...",
    )

    ipnr_tax_zone = fields.Boolean(related="picking_partner_id.ipnr_tax_zone")

    is_dropshipping_ipnr = fields.Boolean(
        "Dropshipping no IPNR", compute="_get_dropshipping_ipnr"
    )

    def _get_dropshipping_ipnr(self):
        for record in self:
            record.is_dropshipping_ipnr = False
            if (
                record.move_type in ["in_invoice", "in_refund"]
                and record.invoice_line_ids.purchase_order_id.dest_address_id
            ):
                record.is_dropshipping_ipnr = (
                    record.invoice_line_ids.purchase_order_id.dest_address_id.ipnr_tax_zone
                )

    @api.depends("state", "plastictax_move_id", "write_date", "invoice_line_ids.is_ipnr")
    def _get_plastic_tax_required(self):
        for record in self:
            show_button = False
            if record.state != "cancel" and record.move_type in [
                "in_invoice",
                "in_refund",
                "out_invoice",
                "out_refund",
            ]:
                for li in record.invoice_line_ids.filtered("is_ipnr"):
                    if li.quantity == 0:
                        continue
                    show_button = True
                    break
            record.plastic_tax = show_button

    plastic_tax = fields.Boolean(
        "Plastic tax", store=False, compute="_get_plastic_tax_required"
    )

    def create_plastic_tax_entry(self):
        if self.plastictax_move_id:
            raise UserError("Esta factura ya tiene un apunte, modifícalo o quita la asociación.")

        company = self.env.company
        plastic_journal = company.plastic_journal_id
        mfg_account = company.plastic_manufacture_account_id
        acq_account = company.plastic_acquirer_account_id

        if not all([plastic_journal, mfg_account, acq_account]):
            raise UserError("Asigna el diario y las cuentas para el impuesto al plástico en la compañía.")

        tax_entry = self.env["account.move"].create({
            "journal_id": plastic_journal.id,
            "move_type": "entry",
            "ref": f"Plastic tax: {self.partner_id.name}",
            "partner_id": self.partner_id.id,
            "invoice_origin": self.invoice_origin,
        })
        self.plastictax_move_id = tax_entry

        line_vals_list = []
        for line in self.invoice_line_ids.filtered("is_ipnr"):
            if line.quantity == 0:
                continue

            debit_account, credit_account = None, None
            move_type = self.move_type
            tax_zone = self.ipnr_tax_zone
            product_type = line.product_id.tax_plastic_type

            if move_type == "out_invoice" and tax_zone:
                if product_type == "manufacturer":
                    debit_account, credit_account = line.account_id, mfg_account
                elif product_type == "acquirer":
                    debit_account, credit_account = line.account_id, acq_account
            elif move_type == "out_invoice" and not tax_zone:
                if product_type == "acquirer":
                    debit_account, credit_account = acq_account, line.account_id
            elif move_type == "out_refund" and tax_zone:
                if product_type == "manufacturer":
                    debit_account, credit_account = mfg_account, line.account_id
                elif product_type == "acquirer":
                    debit_account, credit_account = acq_account, line.account_id
            elif move_type == "out_refund" and not tax_zone:
                if product_type == "acquirer":
                    debit_account, credit_account = line.account_id, acq_account
            elif move_type == "in_invoice" and tax_zone:
                debit_account, credit_account = line.account_id, acq_account
            elif move_type == "in_refund" and tax_zone:
                debit_account, credit_account = acq_account, line.account_id

            if debit_account and credit_account:
                line_vals_list.extend(
                    self._get_tax_entry_line_vals(line, debit_account, credit_account)
                )

        if line_vals_list:
            tax_entry.write({"line_ids": line_vals_list})

    def _get_tax_entry_line_vals(self, line, debit_account, credit_account):
        tax_unit = self.env.company.plastic_tax
        amount = abs(line.quantity * line.product_id.plastic_weight_non_recyclable * tax_unit)
        return [
            (0, 0, {
                "product_id": line.product_id.id,
                "name": line.product_id.name,
                "debit": amount,
                "credit": 0,
                "account_id": debit_account.id,
                "analytic_distribution": line.analytic_distribution,
                "partner_id": self.partner_id.id,
                "quantity": line.quantity * line.product_id.plastic_weight_non_recyclable,
            }),
            (0, 0, {
                "name": self.name or "/",
                "debit": 0,
                "credit": amount,
                "account_id": credit_account.id,
                "partner_id": self.partner_id.id,
            }),
        ]

    @api.constrains("state", "plastictax_move_id")
    def _check_plastic_tax_required(self):
        for record in self:
            if record.state == 'posted' and record.plastic_tax and not record.plastictax_move_id:
                raise UserError("This invoice requires a Plastic Tax entry. Please create it before posting.")

    def action_post(self):
        res = super().action_post()
        for move in self:
            if move.plastictax_move_id and move.plastictax_move_id.state == "draft":
                if move.invoice_date:
                    move.plastictax_move_id.date = move.invoice_date
                should_auto_validate = False
                if move.move_type in ("in_invoice", "in_refund"):
                    should_auto_validate = move.company_id.auto_validate_ipnr_purchase
                elif move.move_type in ("out_invoice", "out_refund"):
                    should_auto_validate = move.company_id.auto_validate_ipnr_sale
                if should_auto_validate:
                    try:
                        move.plastictax_move_id.action_post()
                        _logger.info(
                            f"Apunte IPNR {move.plastictax_move_id.name} validado "
                            f"automáticamente para factura {move.name}"
                        )
                    except Exception as e:
                        _logger.error(
                            f"Error al validar automáticamente apunte IPNR "
                            f"{move.plastictax_move_id.name}: {str(e)}"
                        )
        return res

    def button_draft(self):
        for move in self:
            if move.plastictax_move_id and move.plastictax_move_id.state == "posted":
                try:
                    move.plastictax_move_id.button_draft()
                    _logger.info(
                        f"Apunte IPNR {move.plastictax_move_id.name} pasado a borrador "
                        f"para factura {move.name}"
                    )
                except Exception as e:
                    raise UserError(
                        _("No se pudo pasar a borrador el apunte IPNR %s: %s")
                        % (move.plastictax_move_id.name, str(e))
                    )
        return super().button_draft()

    def button_cancel(self):
        for move in self:
            if move.plastictax_move_id and move.plastictax_move_id.state == "posted":
                try:
                    move.plastictax_move_id.button_draft()
                    _logger.info(
                        f"Apunte IPNR {move.plastictax_move_id.name} pasado a borrador "
                        f"al cancelar factura {move.name}"
                    )
                except Exception as e:
                    raise UserError(
                        _(
                            "No se pudo pasar a borrador el apunte IPNR %s al cancelar: %s"
                        )
                        % (move.plastictax_move_id.name, str(e))
                    )
        return super().button_cancel()
