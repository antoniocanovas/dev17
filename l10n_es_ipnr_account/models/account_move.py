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
        """
        Deletes and recreates the IPNR tax line for the invoice, based on
        lines currently marked with is_ipnr = True.
        This method is the single point of truth for recalculation.
        """
        if self.env.context.get("avoid_recursion"):
            return
        ctx = {**self.env.context, "avoid_recursion": True}

        for move in self:
            # First, delete any existing IPNR tax line to ensure a clean slate.
            move.with_context(ctx)._delete_ipnr()

            # If consolidation is active, let the specific method handle it.
            if move.company_id.ipnr_consolidate_lines:
                move.with_context(ctx)._update_or_create_consolidated_ipnr_line()
                continue

            # If not consolidating, calculate and create the IPNR line.
            if move.is_ipnr:
                lines_to_process = move.invoice_line_ids.filtered("is_ipnr")
                if lines_to_process:
                    ipnr_vals = move._get_ipnr_line_vals(lines_to_process)
                    if ipnr_vals.get("quantity", 0) > 0:
                        self.env["account.move.line"].with_context(ctx).create(ipnr_vals)

    def write(self, vals: object) -> Any:
        res = super().write(vals)
        if "invoice_line_ids" in vals:
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
        help="El impuesto al plástico graba la introducción o fabricación del mismo"
        " en España. \n"
        "- - - \n\n"
        "Es obligatorio el pago de tasa: \n"
        "- En caso de importar plástico. \n"
        "- En caso de fabricar plastico en España. \n"
        "- La tasa de compra se paga adicionalmente al precio del proveedor extranjero,"
        " en aduana. \n"
        "- La repercusión de la tasa al cliente se hace en el PVP, no es compensable y"
        " lleva IVA. \n"
        "- - -  \n\n"
        "Podemos solicitar la devolución de estas tasas en los siguientes casos: \n"
        "- Venta de plástico adquirido fuera de España, pagó tasas y ha sido exportado."
        " \n"
        "- Abono de facturas de compra fuera de España con devolución de material. \n"
        "- - -  \n\n"
        "Otros casos: \n"
        "- Si compramos plástico en España, el proveedor ya pagó la tasa, no podemos"
        " recuperarla. \n"
        "- La compra de materia prima no se considera grabable a que no se conoce"
        " su uso final. \n"
        "- - -  \n\n"
        "CONFIGURACIÓN DE LA APLICACIÓN: \n"
        "- Los productos fabricados están definidos en la familia. \n"
        "- El diario y cuenta contable utilizada para el apunte están definidos "
        "en la configuración de empresa. \n"
        "- En caso de que la factura no requiera tasa el botón para creación"
        " automática no aparece. \n"
        "- Podemos asignar un apunte creado previamente (o nulo) manualmente o"
        " crearlo automáticamente. \n"
        "- Se recomienda diario independiente para facilitar la búsqueda y"
        " filtros oportunos. \n"
        "(más información en la web oficial AEAT) \n",
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
            ) and record.invoice_line_ids.purchase_order_id.dest_address_id.id:
                record.is_dropshipping_ipnr = record.invoice_line_ids.purchase_order_id.dest_address_id.ipnr_tax_zone  # noqa: E501

    @api.depends("state", "plastictax_move_id", "write_date")
    def _get_plastic_tax_required(self):
        show_button = False
        if (self.state not in ["cancel"]) and (
            self.move_type in ["in_invoice", "in_refund", "out_invoice", "out_refund"]
        ):
            for li in self.invoice_line_ids:
                # Con esta condición verificamos que es plástico:
                if (
                    (li.product_id.ipnr_subject != "no")
                    and (li.product_id.plastic_weight_non_recyclable != 0)
                    and (li.quantity != 0)
                ):
                    # Operaciones de compra fuera de España:
                    if (
                        (self.ipnr_tax_zone)
                        and (self.move_type in ["in_invoice", "in_refund"])
                        and not self.invoice_line_ids.purchase_order_id.dest_address_id.id  # noqa: E501
                    ):
                        show_button = True
                    if (
                        (self.move_type in ["in_invoice", "in_refund"])
                        and self.is_dropshipping_ipnr
                        and self.invoice_line_ids.purchase_order_id.dest_address_id.id
                    ):
                        show_button = True
                    # Operaciones de venta fuera de España, sólo recuperamos si es
                    # comercio (no fabricados):
                    if (
                        (self.ipnr_tax_zone)
                        and (self.move_type in ["out_invoice", "out_refund"])
                        and (li.product_id.tax_plastic_type == "acquirer")
                    ):
                        show_button = True
                    # Si vendemos o compramos plástico en España, el impuesto va en
                    # PVP o ya lo pagó el proveedor.
                    # Si vendemos en España plástico PRODUCIDO aquí, hemos de pagar
                    # (si venta en el extranjero, no):
                    if (
                        (self.ipnr_tax_zone)
                        and (self.move_type in ["out_invoice", "out_refund"])
                        and (li.product_id.tax_plastic_type == "manufacturer")
                    ):
                        show_button = True
                    # Si vendemos producto comercializado en Canarias o extranjero,
                    # podemos recuperar el impuesto:
                    if (
                        not (self.ipnr_tax_zone)
                        and (self.move_type in ["out_invoice", "out_refund"])
                        and (li.product_id.tax_plastic_type == "acquirer")
                    ):
                        show_button = True
        self.plastic_tax = show_button

    plastic_tax = fields.Boolean(
        "Plastic tax", store=False, compute="_get_plastic_tax_required"
    )

    def create_plastic_tax_entry(self):
        # Si es venta o abono de compra: el debe a la 700(producto) y haber a la 475
        # Si es compra o abono de venta: el debe a la 475 y haber a la 600
        # (depende del producto)
        # Añadir los kg de plástico
        if self.plastictax_move_id.id:
            raise UserError(
                "Esta factura ya tiene un apunte, modifícalo o quita la asociación."
            )

        plastic_journal = self.env.company.plastic_journal_id
        commercial_account = self.env.company.plastic_acquirer_account_id
        manufacture_account = self.env.company.plastic_manufacture_account_id

        if (
            not (plastic_journal.id)
            or not (commercial_account.id)
            or not (manufacture_account.id)
        ):
            raise UserError(
                "Asigna el diario y cuentas para el impuesto al plástico en la compañía"
            )

        ref = "Plastic tax: " + self.partner_id.name
        tax_entry = self.env["account.move"].create(
            {
                "journal_id": plastic_journal.id,
                "move_type": "entry",
                "ref": ref,
                "partner_id": self.partner_id.id,
                "invoice_origin": self.invoice_origin,
            }
        )
        self.plastictax_move_id = tax_entry

        if (self.move_type == "out_invoice") and (self.ipnr_tax_zone):
            self.tax_entry_out_invoice_spain()
        if (self.move_type == "out_invoice") and not (self.ipnr_tax_zone):
            self.tax_entry_out_invoice_no_spain()

        if (self.move_type == "out_refund") and (self.ipnr_tax_zone):
            self.tax_entry_out_refund_spain()
        if (self.move_type == "out_refund") and not (self.ipnr_tax_zone):
            self.tax_entry_out_refund_no_spain()

        if (self.move_type == "in_invoice") and (self.ipnr_tax_zone):
            self.tax_entry_in_invoice()
        if (self.move_type == "in_refund") and (self.ipnr_tax_zone):
            self.tax_entry_in_refund()

    def tax_entry_out_invoice_spain(self):
        tax_entry = self.plastictax_move_id
        taxproduct = self.env.ref(
            "l10n_es_ipnr_account.aportacion_ipnr_product_template"
        )
        taxline = self.env["account.move.line"].search(
            [("move_id", "=", self.id), ("product_id", "=", taxproduct.id)]
        )
        taxunit = self.env.company.plastic_tax
        quantity = 0

        for line in taxline:
            quantity = +line.quantity

        if quantity > 0:
            for li in self.invoice_line_ids:
                if (
                    (li.product_id.ipnr_subject != "no")
                    and (li.product_id.id)
                    and (li.quantity != 0)
                    and (li.product_id.plastic_weight_non_recyclable != 0)
                    and (li.id not in taxline.ids)
                ):
                    taxplasticaccount = (
                        self.env.company.plastic_manufacture_account_id.id
                    )
                    if li.product_id.tax_plastic_type == "acquirer":
                        taxplasticaccount = (
                            self.env.company.plastic_acquirer_account_id.id
                        )

                    tax_entry["line_ids"] = [
                        (
                            0,
                            0,
                            {
                                "product_id": li.product_id.id,
                                "display_type": li.display_type,
                                "name": li.product_id.name,
                                "price_unit": abs(taxunit),
                                "debit": abs(
                                    li.quantity
                                    * li.product_id.plastic_weight_non_recyclable
                                    * taxunit
                                ),
                                "account_id": li.account_id.id,
                                "analytic_distribution": li.analytic_distribution,
                                "partner_id": self.partner_id.id,
                                "quantity": li.quantity
                                * li.product_id.plastic_weight_non_recyclable,
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "name": self.name or "/",
                                "credit": abs(
                                    li.quantity
                                    * li.product_id.plastic_weight_non_recyclable
                                    * taxunit
                                ),
                                "account_id": taxplasticaccount,
                                "partner_id": self.partner_id.id,
                            },
                        ),
                    ]

    def tax_entry_out_invoice_no_spain(self):
        # En la venta reclamamos abono de impuesto pagado si vendemos
        # fabricados IMPORTADOS (que pagamos en aduana anteriormente la tasa):
        tax_entry = self.plastictax_move_id
        taxproduct = self.env.ref(
            "l10n_es_ipnr_account.aportacion_ipnr_product_template"
        )
        taxline = self.env["account.move.line"].search(
            [("move_id", "=", self.id), ("product_id", "=", taxproduct.id)]
        )
        taxunit = self.env.company.plastic_tax

        for li in self.invoice_line_ids:
            if (
                (li.product_id.ipnr_subject != "no")
                and (li.product_id.id)
                and (li.quantity != 0)
                and (li.product_id.plastic_weight_non_recyclable != 0)
                and (li.id != taxline.id)
                and (li.product_id.tax_plastic_type == "acquirer")
            ):
                tax_entry["line_ids"] = [
                    (
                        0,
                        0,
                        {
                            "product_id": li.product_id.id,
                            "display_type": li.display_type,
                            "name": li.product_id.name,
                            "price_unit": abs(taxunit),
                            "credit": abs(
                                li.quantity
                                * li.product_id.plastic_weight_non_recyclable
                                * taxunit
                            ),
                            "account_id": li.account_id.id,
                            "analytic_distribution": li.analytic_distribution,
                            "partner_id": self.partner_id.id,
                            "quantity": li.quantity
                            * li.product_id.plastic_weight_non_recyclable,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": self.name or "/",
                            "debit": abs(
                                li.quantity
                                * li.product_id.plastic_weight_non_recyclable
                                * taxunit
                            ),
                            "account_id": self.env.company.plastic_acquirer_account_id.id,  # noqa: E501
                            "partner_id": self.partner_id.id,
                        },
                    ),
                ]

    def tax_entry_out_refund_spain(self):
        tax_entry = self.plastictax_move_id
        taxproduct = self.env.ref(
            "l10n_es_ipnr_account.aportacion_ipnr_product_template"
        )
        taxline = self.env["account.move.line"].search(
            [("move_id", "=", self.id), ("product_id", "=", taxproduct.id)]
        )
        taxunit = self.env.company.plastic_tax

        for li in self.invoice_line_ids:
            if (
                (li.product_id.ipnr_subject != "no")
                and (li.product_id.id)
                and (li.quantity != 0)
                and (li.product_id.plastic_weight_non_recyclable != 0)
                and (li.id != taxline.id)
            ):
                taxplasticaccount = self.env.company.plastic_manufacture_account_id.id
                if li.product_id.tax_plastic_type == "acquirer":
                    taxplasticaccount = self.env.company.plastic_acquirer_account_id.id

                tax_entry["line_ids"] = [
                    (
                        0,
                        0,
                        {
                            "product_id": li.product_id.id,
                            "display_type": li.display_type,
                            "name": li.product_id.name,
                            "price_unit": abs(taxunit),
                            "debit": abs(
                                li.quantity
                                * li.product_id.plastic_weight_non_recyclable
                                * taxunit
                            ),
                            "account_id": taxplasticaccount,
                            "analytic_distribution": li.analytic_distribution,
                            "partner_id": self.partner_id.id,
                            "quantity": li.quantity
                            * li.product_id.plastic_weight_non_recyclable,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": self.name or "/",
                            "credit": abs(
                                li.quantity
                                * li.product_id.plastic_weight_non_recyclable
                                * taxunit
                            ),
                            "account_id": li.account_id.id,
                            "partner_id": self.partner_id.id,
                        },
                    ),
                ]

    def tax_entry_out_refund_no_spain(self):
        # En venta si nos han devuelto el impuesto (porque pagamos "no fabricado"
        # hemos de volver a pagarlo ya que introducimos plático en España:
        tax_entry = self.plastictax_move_id
        taxproduct = self.env.ref(
            "l10n_es_ipnr_account.aportacion_ipnr_product_template"
        )
        taxline = self.env["account.move.line"].search(
            [("move_id", "=", self.id), ("product_id", "=", taxproduct.id)]
        )
        taxunit = self.env.company.plastic_tax

        if taxline.quantity > 0:
            for li in self.invoice_line_ids:
                if (
                    (li.product_id.ipnr_subject != "no")
                    and (li.product_id.id)
                    and (li.quantity != 0)
                    and (li.product_id.plastic_weight_non_recyclable != 0)
                    and (li.id != taxline.id)
                ):
                    tax_entry["line_ids"] = [
                        (
                            0,
                            0,
                            {
                                "product_id": li.product_id.id,
                                "display_type": li.display_type,
                                "name": li.product_id.name,
                                "price_unit": abs(taxunit),
                                "credit": abs(
                                    li.quantity
                                    * li.product_id.plastic_weight_non_recyclable
                                    * taxunit
                                ),
                                "account_id": self.env.company.plastic_acquirer_account_id.id,  # noqa: E501
                                "analytic_distribution": li.analytic_distribution,
                                "partner_id": self.partner_id.id,
                                "quantity": li.quantity
                                * li.product_id.plastic_weight_non_recyclable,
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "name": self.name or "/",
                                "debit": abs(
                                    li.quantity
                                    * li.product_id.plastic_weight_non_recyclable
                                    * taxunit
                                ),
                                "account_id": li.account_id.id,
                                "partner_id": self.partner_id.id,
                            },
                        ),
                    ]

    def tax_entry_in_invoice(self):
        # Pagamos impuesto en aduana por Compra de plástico en el extranjero
        # (la materia prima no paga, para
        # esto en los productos de materia prima "plastic_weight_non_recyclable" == 0):
        tax_entry = self.plastictax_move_id
        taxproduct = self.env.ref(
            "l10n_es_ipnr_account.aportacion_ipnr_product_template"
        )
        taxline = self.env["account.move.line"].search(
            [("move_id", "=", self.id), ("product_id", "=", taxproduct.id)]
        )
        taxunit = self.env.company.plastic_tax

        # Si estamos en España, las lineas vienen de compras o calcula
        # automáticamente por is_ipnr:
        # Si compramos fuera, no habrá línea de impuestos:
        #                if (taxline.quantity > 0) (cambio 21/01/25):
        if self.plastic_tax:
            for li in self.invoice_line_ids:
                if (
                    (li.product_id.ipnr_subject != "no")
                    and (li.product_id.id)
                    and (li.quantity != 0)
                    and (li.product_id.plastic_weight_non_recyclable != 0)
                    and (li.id != taxline.id)
                ):
                    tax_entry["line_ids"] = [
                        (
                            0,
                            0,
                            {
                                "product_id": li.product_id.id,
                                "display_type": li.display_type,
                                "name": li.product_id.name,
                                "price_unit": abs(taxunit),
                                "debit": abs(
                                    li.quantity
                                    * li.product_id.plastic_weight_non_recyclable
                                    * taxunit
                                ),
                                "account_id": li.account_id.id,
                                "analytic_distribution": li.analytic_distribution,
                                "partner_id": self.partner_id.id,
                                "quantity": li.quantity
                                * li.product_id.plastic_weight_non_recyclable,
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "name": self.name or "/",
                                "credit": abs(
                                    li.quantity
                                    * li.product_id.plastic_weight_non_recyclable
                                    * taxunit
                                ),
                                "account_id": self.env.company.plastic_acquirer_account_id.id,  # noqa: E501
                                "partner_id": self.partner_id.id,
                            },
                        ),
                    ]

    def tax_entry_in_refund(self):
        # Abono del anterior,
        # Solicitud de devolución de impuesto en aduana por Compra de plástico en el
        # extranjero:
        tax_entry = self.plastictax_move_id
        taxproduct = self.env.ref(
            "l10n_es_ipnr_account.aportacion_ipnr_product_template"
        )
        taxline = self.env["account.move.line"].search(
            [("move_id", "=", self.id), ("product_id", "=", taxproduct.id)]
        )
        taxunit = self.env.company.plastic_tax

        # if (taxline.quantity > 0) (cambio 21/01/25):
        if self.plastic_tax:
            for li in self.invoice_line_ids:
                if (
                    (li.product_id.ipnr_subject != "no")
                    and (li.product_id.id)
                    and (li.quantity != 0)
                    and (li.product_id.plastic_weight_non_recyclable != 0)
                    and (li.id != taxline.id)
                ):
                    tax_entry["line_ids"] = [
                        (
                            0,
                            0,
                            {
                                "product_id": li.product_id.id,
                                "display_type": li.display_type,
                                "name": li.product_id.name,
                                "price_unit": abs(taxunit),
                                "debit": abs(
                                    li.quantity
                                    * li.product_id.plastic_weight_non_recyclable
                                    * taxunit
                                ),
                                "account_id": self.env.company.plastic_acquirer_account_id.id,  # noqa: E501
                                "analytic_distribution": li.analytic_distribution,
                                "partner_id": self.partner_id.id,
                                "quantity": li.quantity
                                * li.product_id.plastic_weight_non_recyclable,
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "name": self.name or "/",
                                "credit": abs(
                                    li.quantity
                                    * li.product_id.plastic_weight_non_recyclable
                                    * taxunit
                                ),
                                "account_id": li.account_id.id,
                                "partner_id": self.partner_id.id,
                            },
                        ),
                    ]

    # Caso 1.- Compramos plástico fuera de España => Impuesto (contemplado)
    # Caso 2.- Compramos plástico dentro de España => Ese plástico ya pagó impuesto
    # (contemplado)
    # Caso 3.- Vendemos en España algo comprado fuera y pagó impuesto => Cobrar al
    # cliente en pvp (contemplado)
    # Caso 4.- Vendemos fuera algo comprado fuera de España => Reclamar impuesto ya
    # pagado (contemplado)
    # Caso 5.- Vendemos fuera algo fabricando por nosotros => No paga impuestos
    # (contemplado en tarifa + constrains)

    @api.constrains("state", "plastictax_move_id")
    def _check_plastic_tax_required(self):  # noqa: C901
        for record in self:
            if (record.move_type in ["in_invoice", "in_refund"]) and (
                record.state in ["posted"]
            ):
                # Control de que el cliente tiene asignado el país y provincia si es en
                # España (por la exclusión Canaria):
                if not record.picking_partner_id.country_id.id:
                    raise UserError(
                        "Pon el país al proveedor para poder controlar el impuesto al"
                        " plástico: " + record.picking_partner_id.name
                    )
                if (not record.picking_partner_id.state_id.id) and (
                    record.picking_partner_id.country_id.code == "ES"
                ):
                    raise UserError(
                        "Pon la provincia al proveedor para poder controlar el impuesto"
                        " al plástico: " + record.picking_partner_id.name
                    )

                # Si el país es España quien vende ha pagado impuesto y no podemos
                # repercutirlo, si extranjero hemos de pagar:
                if (record.ipnr_tax_zone) and not (record.plastictax_move_id.id):
                    for li in record.invoice_line_ids:
                        if (li.product_id.ipnr_subject != "no") and (
                            li.product_id.plastic_weight_non_recyclable != 0
                        ):
                            message = (
                                "El producto "
                                + li.product_id.name
                                + " requiere impuesto al plástico, crea o asigna el"
                                " apunte correspondiente en esta factura"
                            )
                            raise UserError(message)

            if (record.move_type in ["out_invoice", "out_refund"]) and (
                record.state in ["posted"]
            ):
                # Control de que el cliente tiene asignado el país:
                if not record.picking_partner_id.country_id.id:
                    raise UserError(
                        "Pon el país al cliente para poder controlar el impuesto "
                        "al plástico."
                    )
                if (not record.picking_partner_id.state_id.id) and (
                    record.picking_partner_id.country_id.code == "ES"
                ):
                    raise UserError(
                        "Pon la provincia al cliente para poder controlar el impuesto "
                        "al plástico: " + record.picking_partner_id.name
                    )
                # Si es cliente extranjero y el plástico fue importado pagando tasas,
                # podemos recuperar el importe:
                if not (record.ipnr_tax_zone) and not (record.plastictax_move_id.id):
                    for li in record.invoice_line_ids:
                        if (
                            (li.product_id.ipnr_subject != "no")
                            and (li.product_id.plastic_weight_non_recyclable != 0)
                            and (li.product_id.tax_plastic_type == "acquirer")
                        ):
                            message = (
                                "El producto "
                                + li.product_id.name
                                + " es susceptible de recuperar el impuesto al"
                                " plástico,"
                                " crea o asigna el apunte correspondiente en"
                                " esta factura"
                            )
                            raise UserError(message)
                # Caso de venta en España de plástico fabricado por nosotros en España,
                # requiere impuesto:
                if (record.ipnr_tax_zone) and not (record.plastictax_move_id.id):
                    for li in record.invoice_line_ids:
                        if (
                            (li.product_id.ipnr_subject != "no")
                            and (li.product_id.plastic_weight_non_recyclable != 0)
                            and (li.product_id.tax_plastic_type == "manufacturer")
                        ):
                            message = (
                                "El producto "
                                + li.product_id.name
                                + " requiere impuesto al plástico, crea o asigna el"
                                " apunte correspondiente en esta factura"
                            )
                            raise UserError(message)

    def manage_sale_ipnr_lines(self):
        """
        Sobrescribe manage_sale_ipnr_lines de l10n_es_ipnr_sale.

        Si la consolidación está activa:
        - Crea/actualiza UNA única línea IPNR consolidada para todos los pedidos

        Si la consolidación NO está activa:
        - Ejecuta la lógica original (una línea IPNR por pedido)
        """
        if self.company_id.ipnr_consolidate_lines:
            # Crear/actualizar UNA línea IPNR consolidada
            self._update_or_create_consolidated_ipnr_line()
            return

        # Lógica original: una línea por pedido
        return super().manage_sale_ipnr_lines()

    def manage_ipnr_invoice_lines(self):
        """
        Sobrescribe manage_ipnr_invoice_lines de l10n_es_ipnr_account.

        Este método gestiona las líneas que NO vienen de pedidos (añadidas manualmente).

        Si la consolidación está activa:
        - Actualiza la línea IPNR consolidada existente

        Si la consolidación NO está activa:
        - Ejecuta la lógica original (crea línea IPNR separada)
        """
        if self.company_id.ipnr_consolidate_lines:
            # Actualizar línea IPNR consolidada con nuevas líneas manuales
            self._update_or_create_consolidated_ipnr_line()
            return

        # Lógica original: crea línea IPNR separada para líneas independientes
        return super().manage_ipnr_invoice_lines()

    def _update_or_create_consolidated_ipnr_line(self):
        """
        Crea o actualiza una única línea IPNR consolidada.

        IMPORTANTE: Primero elimina TODAS las líneas IPNR existentes para evitar
        duplicados cuando se mezclan líneas de pedidos y líneas manuales.

        Esta línea incluye el peso de:
        - TODAS las líneas que vienen de pedidos (con sale_line_ids)
        - TODAS las líneas añadidas manualmente (sin sale_line_ids)

        Consolida todo en UNA SOLA línea IPNR.
        """
        self.ensure_one()

        # Obtener producto IPNR
        ipnr_product = self.env.ref(
            "l10n_es_ipnr_account.aportacion_ipnr_product_template",
            raise_if_not_found=False,
        )

        if not ipnr_product:
            return

        # PASO 1: Eliminar TODAS las líneas IPNR existentes primero
        # Esto evita que se acumulen líneas de diferentes flujos
        existing_ipnr_lines = self.invoice_line_ids.filtered(
            lambda l: l.product_id == ipnr_product
        )
        if existing_ipnr_lines:
            _logger.debug(
                f"Eliminando {len(existing_ipnr_lines)} línea(s) IPNR existente(s) "
                f"antes de consolidar"
            )
            existing_ipnr_lines.unlink()

        # PASO 2: Buscar TODAS las líneas con productos sujetos a IPNR
        # (tanto de pedidos como manuales)
        all_lines_with_ipnr = self.invoice_line_ids.filtered("is_ipnr")

        if not all_lines_with_ipnr:
            # Si no hay líneas con IPNR, no crear nada
            _logger.debug("No hay líneas con productos IPNR, no se crea línea IPNR")
            return

        # PASO 3: Calcular peso total de TODAS las líneas
        total_weight = sum(
            line.product_uom_id._compute_quantity(line.quantity, line.product_id.uom_id)
            * line.product_id.plastic_weight_non_recyclable
            for line in all_lines_with_ipnr
        )

        if total_weight <= 0:
            _logger.debug("Peso total IPNR es 0, no se crea línea IPNR")
            return

        # PASO 4: Obtener precio IPNR
        date = self.ipnr_default_date(all_lines_with_ipnr)
        price_unit = self.env["l10n.es.ipnr.amount"].get_ipnr_amount(date)

        # PASO 5: Recopilar TODAS las sale_line_ids de líneas IPNR en los pedidos
        # (solo para líneas que vienen de pedidos)
        lines_from_orders = all_lines_with_ipnr.filtered(lambda l: l.sale_line_ids)
        all_ipnr_sale_lines = []
        if lines_from_orders:
            all_ipnr_sale_lines = lines_from_orders.mapped(
                "sale_line_ids.order_id.order_line"
            ).filtered(lambda a: a.is_ipnr)

        # PASO 6: Crear la nueva línea IPNR consolidada
        kg_uom = self.env.ref("uom.product_uom_kgm")

        vals = {
            "move_id": self.id,
            "product_id": ipnr_product.id,
            "name": ipnr_product.name,
            "quantity": total_weight,
            "product_uom_id": kg_uom.id,
            "price_unit": price_unit,
            "sequence": 10000,
        }

        # Obtener configuración de cuenta e impuestos desde el producto
        fiscal_position = self.fiscal_position_id
        accounts = ipnr_product.product_tmpl_id.get_product_accounts(
            fiscal_pos=fiscal_position
        )
        if accounts["income"]:
            vals["account_id"] = accounts["income"].id

        # Añadir impuestos si aplican
        if ipnr_product.taxes_id:
            vals["tax_ids"] = [(6, 0, ipnr_product.taxes_id.ids)]

        # Añadir trazabilidad con líneas IPNR de los pedidos si existen
        if all_ipnr_sale_lines:
            vals["sale_line_ids"] = [(6, 0, all_ipnr_sale_lines.ids)]

        self.env["account.move.line"].create(vals)

        _logger.info(
            f"✓ Línea IPNR consolidada en {self.name or 'BORRADOR'}: "
            f"{total_weight:.3f} kg × {price_unit:.2f}€ = "
            f"{total_weight * price_unit:.2f}€ "
            f"({len(all_lines_with_ipnr)} línea(s) de producto)"
        )

    def action_post(self):
        """
        Sobrescribe action_post para validar automáticamente el apunte IPNR
        según la configuración de la empresa.
        """
        # Ejecutar validación estándar
        res = super().action_post()

        # Auto-validar apunte IPNR si está configurado
        for move in self:
            if move.plastictax_move_id and move.plastictax_move_id.state == "draft":
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
        """
        Sobrescribe button_draft para pasar a borrador el apunte IPNR
        cuando la factura vuelve a borrador.
        """
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
        """
        Sobrescribe button_cancel para pasar a borrador el apunte IPNR
        cuando la factura se cancela.
        """
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
