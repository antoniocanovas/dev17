# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _
from odoo.osv import expression
from odoo.exceptions import UserError

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

    @api.depends(
        "company_id",
        "fiscal_position_id",
        "move_type",
    )
    def _compute_is_ipnr(self):
        for record in self:
            is_ipnr = False
            # PARA LAS COMPRAS:
#            if (record.move_type in ['in_invoice', 'in_refund']):
                # Control de que el destino de la compra va a España o no está definido:
                # Eliminado 21/01/25 porque las facturas de extranjero no indican  impuesto, lo haremos en apunte externo:
#                if ((record.partner_id.country_id.code != 'ES') and
#                        (not record.picking_partner_id.country_id.id or
                        #Se comenta la provincia porque no todos los países tienen (15/01/25):
                        #not record.picking_partner_id.state_id.id or
#                        record.ipnr_tax_zone == True)):
#                    is_ipnr = True

            # PARA LAS VENTAS:
            if ((record.move_type in ['out_invoice', 'out_refund']) and
                (not record.picking_partner_id.country_id.id or
                 # Se comenta la provincia porque no todos los países tienen (15/01/25):
                 #not record.picking_partner_id.state_id.id or
                 record.ipnr_tax_zone)):
                is_ipnr = True

            record.is_ipnr = is_ipnr

    @api.depends("is_ipnr", "invoice_date", "company_id")
    def _compute_ipnr_is_date(self):
        ret = super()._compute_ipnr_is_date()
        for rec in self.filtered(
            lambda a: a.is_ipnr
            and not a.invoice_date
            and a.company_id.ipnr_date_from
        ):
            rec.ipnr_is_date = (
                rec.create_date.date() >= rec.company_id.ipnr_date_from
            )
        return ret

    @api.depends("invoice_line_ids")
    def _compute_ipnr_has_line(self):
        return super()._compute_ipnr_has_line()

    @api.depends("company_id")
    def _compute_ipnr_company(self):
        return super()._compute_ipnr_company()

    def ipnr_default_date(self, lines):
        self.ensure_one()
        return self.invoice_date or self.create_date.date()

    @api.model
    def get_independent_invoice_lines_domain(self):
        """
        Override this method to get the invoice lines not related to other
        models (i.e. sale orders)
        """
        return []

    def manage_ipnr_invoice_lines(self):
        self.ensure_one()
        independent_lines_domain = self.get_independent_invoice_lines_domain()
        independent_ipnr_lines_domain = expression.AND(
            [
                [
                    ("move_id", "=", self.id),
                    ("is_ipnr", "=", True),
                ],
                independent_lines_domain,
            ]
        )
        self.env["account.move.line"].search(independent_ipnr_lines_domain).unlink()
        # Invoice lines not related to other documents (i.e. sales)
        independent_lines_domain = expression.AND(
            [
                [
                    ("move_id", "=", self.id),
                    ("product_id", "!=", False),
                    ("product_id.ipnr_has_amount", "=", True),
                ],
                independent_lines_domain,
            ]
        )
        independent_lines = self.env["account.move.line"].search(
            independent_lines_domain
        )
        if independent_lines:
            self.create_ipnr_line(independent_lines)

    def create_ipnr_line(self, lines, **kwargs):
        values = self._get_ipnr_line_vals(lines, **kwargs)
        self.env["account.move.line"].create(values)

    def apply_ipnr(self):
        for invoice in self.filtered(
            lambda a: a.state == "draft" and a.is_ipnr and a.ipnr_is_date and a.id
        ):
            invoice.automatic_ipnr_exception()
            invoice.with_context(avoid_recursion=True).manage_ipnr_invoice_lines()

    def write(self, vals):
        res = super().write(vals)
        if any(
            value in list(vals.keys())
            for value in [
                "is_ipnr",
                "company_id",
                "fiscal_position_id",
                "invoice_line_ids",
                "move_type",
                "invoice_date",
            ]
        ):
            self.with_context(avoid_recursion=True)._delete_ipnr()
            self.apply_ipnr()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        for move in moves.filtered(lambda a: a.is_ipnr and a.ipnr_is_date):
            move.automatic_ipnr_exception()
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

    plastictax_move_id = fields.Many2one('account.move', store=True, string='Plastic tax entry', copy=False,
                                 help='El impuesto al plástico graba la introducción o fabricación del mismo en España. \n'
                                      '- - - \n\n'
                                      'Es obligatorio el pago de tasa: \n'
                                      '- En caso de importar plástico. \n'
                                      '- En caso de fabricar plastico en España. \n'
                                      '- La tasa de compra se paga adicionalmente al precio del proveedor extranjero, en aduana. \n'
                                      '- La repercusión de la tasa al cliente se hace en el PVP, no es compensable y lleva IVA. \n'
                                      '- - -  \n\n'
                                      'Podemos solicitar la devolución de estas tasas en los siguientes casos: \n'
                                      '- Venta de plástico adquirido fuera de España, pagó tasas y ha sido exportado. \n'
                                      '- Abono de facturas de compra fuera de España con devolución de material. \n'
                                      '- - -  \n\n'
                                      'Otros casos: \n'
                                      '- Si compramos plástico en España, el proveedor ya pagó la tasa, no podemos recuperarla. \n'
                                      '- La compra de materia prima no se considera grabable a que no se conoce su uso final. \n'
                                      '- - -  \n\n'
                                      'CONFIGURACIÓN DE LA APLICACIÓN: \n'
                                      '- Los productos fabricados están definidos en la familia. \n'
                                      '- El diario y cuenta contable utilizada para el apunte están definidos en la configuración de empresa. \n'
                                      '- En caso de que la factura no requiera tasa el botón para creación automática no aparece. \n'
                                      '- Podemos asignar un apunte creado previamente (o nulo) manualmente o crearlo automáticamente. \n'
                                      '- Se recomienda diario independiente para facilitar la búsqueda y filtros oportunos. \n'
                                      '(más información en la web oficial AEAT) \n')

    ipnr_tax_zone = fields.Boolean(related='picking_partner_id.ipnr_tax_zone')

    @api.depends('state', 'plastictax_move_id', 'write_date')
    def _get_plastic_tax_required(self):
        show_button = False
        if (self.state not in ['cancel']) and (self.move_type in ['in_invoice','in_refund','out_invoice','out_refund']):
            for li in self.invoice_line_ids:
                # Con esta condición verificamos que es plástico:
                if (li.product_id.ipnr_subject != 'no') and (li.product_id.plastic_weight_non_recyclable != 0) and (li.quantity != 0):
                    # Operaciones de compra fuera de España:
                    if (self.ipnr_tax_zone) and (self.move_type in ['in_invoice','in_refund']):
                        show_button = True
                    # Operaciones de venta fuera de España, sólo recuperamos si es comercio (no fabricados):
                    if (self.ipnr_tax_zone) and (self.move_type in ['out_invoice','out_refund']) and (li.product_id.tax_plastic_type == 'acquirer'):
                        show_button = True
                    # Si vendemos o compramos plástico en España, el impuesto va en PVP o ya lo pagó el proveedor.
                    # Si vendemos en España plástico PRODUCIDO aquí, hemos de pagar (si venta en el extranjero, no):
                    if (self.ipnr_tax_zone) and (self.move_type in ['out_invoice','out_refund']) and (li.product_id.tax_plastic_type == 'manufacturer'):
                        show_button = True
                    # Si vendemos producto comercializado en Canarias o extranjero, podemos recuperar el impuesto:
                    if not (self.ipnr_tax_zone) and (self.move_type in ['out_invoice','out_refund']) and (li.product_id.tax_plastic_type == 'acquirer'):
                        show_button = True
        self.plastic_tax = show_button
    plastic_tax = fields.Boolean('Plastic tax', store=False, compute='_get_plastic_tax_required')

    def create_plastic_tax_entry(self):
        # Si es venta o abono de compra: el debe a la 700(producto) y haber a la 475
        # Si es compra o abono de venta: el debe a la 475 y haber a la 600 (depende del producto)
        # Añadir los kg de plástico
        if self.plastictax_move_id.id:
          raise UserError('Esta factura ya tiene un apunte, modifícalo o quita la asociación.')

        plastic_journal = self.env.company.plastic_journal_id
        commercial_account = self.env.company.plastic_acquirer_account_id
        manufacture_account = self.env.company.plastic_manufacture_account_id

        if not (plastic_journal.id) or not (commercial_account.id) or not (manufacture_account.id):
            raise UserError('Asigna el diario y cuentas para el impuesto al plástico en la compañía.')

        ref = "Plastic tax: " + self.partner_id.name
        tax_entry = self.env['account.move'].create(
            {'journal_id': plastic_journal.id, 'move_type': 'entry', 'ref': ref,
             'partner_id': self.partner_id.id, 'invoice_origin': self.invoice_origin})
        self.plastictax_move_id = tax_entry

        control = 0
        if (self.move_type == 'out_invoice') and (self.ipnr_tax_zone):
            self.tax_entry_out_invoice_spain()
        if (self.move_type == 'out_invoice') and not (self.ipnr_tax_zone):
            self.tax_entry_out_invoice_no_spain()

        if (self.move_type == 'out_refund') and (self.ipnr_tax_zone):
            self.tax_entry_out_refund_spain()
        if (self.move_type == 'out_refund') and not (self.ipnr_tax_zone):
            self.tax_entry_out_refund_no_spain()

        if (self.move_type == 'in_invoice') and (self.ipnr_tax_zone):
            self.tax_entry_in_invoice()
        if (self.move_type == 'in_refund') and (self.ipnr_tax_zone):
            self.tax_entry_in_refund()

    def tax_entry_out_invoice_spain(self):
        tax_entry = self.plastictax_move_id
        taxproduct = self.env.ref('l10n_es_ipnr_account.aportacion_ipnr_product_template')
        taxline = self.env['account.move.line'].search([('move_id', '=', self.id), ('product_id', '=', taxproduct.id)])
        taxunit = self.env.company.plastic_tax

        if (taxline.quantity > 0):
            for li in self.invoice_line_ids:
                if ((li.product_id.ipnr_subject != 'no') and (li.product_id.id) and (li.quantity != 0) and
                        (li.product_id.plastic_weight_non_recyclable != 0) and (li.id != taxline.id)):

                    taxplasticaccount = self.env.company.plastic_manufacture_account_id.id
                    if li.product_id.tax_plastic_type == 'acquirer':
                        taxplasticaccount = self.env.company.plastic_acquirer_account_id.id

                    tax_entry['line_ids'] = [(0, 0, {
                        'product_id': li.product_id.id,
                        'display_type': li.display_type,
                        'name': li.product_id.name,
                        'price_unit': abs(taxunit),
                        'debit': abs(li.quantity * li.product_id.plastic_weight_non_recyclable * taxunit),
                        'account_id': li.account_id.id,
                        'analytic_distribution': li.analytic_distribution,
                        'partner_id': self.partner_id.id,
                        'quantity': li.quantity * li.product_id.plastic_weight_non_recyclable,
                    }), (0, 0, {
                        'name': self.name or '/',
                        'credit': abs(li.quantity * li.product_id.plastic_weight_non_recyclable * taxunit),
                        'account_id': taxplasticaccount,
                        'partner_id': self.partner_id.id,
                    })]


    def tax_entry_out_invoice_no_spain(self):
        # En la venta reclamamos abono de impuesto pagado si vendemos fabricados IMPORTADOS (que pagamos en aduana anteriormente la tasa):
        tax_entry = self.plastictax_move_id
        taxproduct = self.env.ref('l10n_es_ipnr_account.aportacion_ipnr_product_template')
        taxline = self.env['account.move.line'].search([('move_id', '=', self.id), ('product_id', '=', taxproduct.id)])
        taxunit = self.env.company.plastic_tax

        for li in self.invoice_line_ids:
            if ((li.product_id.ipnr_subject != 'no') and (li.product_id.id) and (li.quantity != 0) and
                    (li.product_id.plastic_weight_non_recyclable != 0) and (li.id != taxline.id) and
                    (li.product_id.tax_plastic_type == 'acquirer')):
                tax_entry['line_ids'] = [(0, 0, {
                    'product_id': li.product_id.id,
                    'display_type': li.display_type,
                    'name': li.product_id.name,
                    'price_unit': abs(taxunit),
                    'credit': abs(li.quantity * li.product_id.plastic_weight_non_recyclable * taxunit),
                    'account_id': li.account_id.id,
                    'analytic_distribution': li.analytic_distribution,
                    'partner_id': self.partner_id.id,
                    'quantity': li.quantity * li.product_id.plastic_weight_non_recyclable,
                }), (0, 0, {
                    'name': self.name or '/',
                    'debit': abs(li.quantity * li.product_id.plastic_weight_non_recyclable * taxunit),
                    'account_id': self.env.company.plastic_acquirer_account_id.id,
                    'partner_id': self.partner_id.id,
                })]



    def tax_entry_out_refund_spain(self):
        tax_entry = self.plastictax_move_id
        taxproduct = self.env.ref('l10n_es_ipnr_account.aportacion_ipnr_product_template')
        taxline = self.env['account.move.line'].search([('move_id', '=', self.id), ('product_id', '=', taxproduct.id)])
        taxunit = self.env.company.plastic_tax

        for li in self.invoice_line_ids:
            if ((li.product_id.ipnr_subject != 'no') and (li.product_id.id) and (li.quantity != 0) and
                    (li.product_id.plastic_weight_non_recyclable != 0) and (li.id != taxline.id)):

                taxplasticaccount = self.env.company.plastic_manufacture_account_id.id
                if li.product_id.tax_plastic_type == 'acquirer':
                    taxplasticaccount = self.env.company.plastic_acquirer_account_id.id

                tax_entry['line_ids'] = [(0, 0, {
                    'product_id': li.product_id.id,
                    'display_type': li.display_type,
                    'name': li.product_id.name,
                    'price_unit': abs(taxunit),
                    'debit': abs(li.quantity * li.product_id.plastic_weight_non_recyclable * taxunit),
                    'account_id': taxplasticaccount,
                    'analytic_distribution': li.analytic_distribution,
                    'partner_id': self.partner_id.id,
                    'quantity': li.quantity * li.product_id.plastic_weight_non_recyclable,
                }), (0, 0, {
                    'name': self.name or '/',
                    'credit': abs(li.quantity * li.product_id.plastic_weight_non_recyclable * taxunit),
                    'account_id': li.account_id.id,
                    'partner_id': self.partner_id.id,
                })]

    def tax_entry_out_refund_no_spain(self):
        # En venta si nos han devuelto el impuesto (porque pagamos "no fabricado"
        # hemos de volver a pagarlo ya que introducimos plático en España:
        tax_entry = self.plastictax_move_id
        taxproduct = self.env.ref('l10n_es_ipnr_account.aportacion_ipnr_product_template')
        taxline = self.env['account.move.line'].search([('move_id', '=', self.id), ('product_id', '=', taxproduct.id)])
        taxunit = self.env.company.plastic_tax

        if (taxline.quantity > 0):
            for li in self.invoice_line_ids:
                if ((li.product_id.ipnr_subject != 'no') and (li.product_id.id) and (li.quantity != 0) and
                        (li.product_id.plastic_weight_non_recyclable != 0) and (li.id != taxline.id)):
                    tax_entry['line_ids'] = [(0, 0, {
                        'product_id': li.product_id.id,
                        'display_type': li.display_type,
                        'name': li.product_id.name,
                        'price_unit': abs(taxunit),
                        'credit': abs(li.quantity * li.product_id.plastic_weight_non_recyclable * taxunit),
                        'account_id': self.env.company.plastic_acquirer_account_id.id,
                        'analytic_distribution': li.analytic_distribution,
                        'partner_id': self.partner_id.id,
                        'quantity': li.quantity * li.product_id.plastic_weight_non_recyclable,
                    }), (0, 0, {
                        'name': self.name or '/',
                        'debit': abs(li.quantity * li.product_id.plastic_weight_non_recyclable * taxunit),
                        'account_id': li.account_id.id,
                        'partner_id': self.partner_id.id,
                    })]


    def tax_entry_in_invoice(self):
                # Pagamos impuesto en aduana por Compra de plástico en el extranjero (la materia prima no paga, para
                # esto en los productos de materia prima "plastic_weight_non_recyclable" == 0):
                tax_entry = self.plastictax_move_id
                taxproduct = self.env.ref('l10n_es_ipnr_account.aportacion_ipnr_product_template')
                taxline = self.env['account.move.line'].search(
                    [('move_id', '=', self.id), ('product_id', '=', taxproduct.id)])
                taxunit = self.env.company.plastic_tax

                # Si estamos en España, las lineas vienen de compras o calcula automáticamente por is_ipnr:
                # Si compramos fuera, no habrá línea de impuestos:
#                if (taxline.quantity > 0) (cambio 21/01/25):
                if self.plastic_tax:
                    for li in self.invoice_line_ids:
                        if ((li.product_id.ipnr_subject != 'no') and (li.product_id.id) and (li.quantity != 0) and
                                (li.product_id.plastic_weight_non_recyclable != 0) and (li.id != taxline.id)):
                            tax_entry['line_ids'] = [(0, 0, {
                                'product_id': li.product_id.id,
                                'display_type': li.display_type,
                                'name': li.product_id.name,
                                'price_unit': abs(taxunit),
                                'debit': abs(li.quantity * li.product_id.plastic_weight_non_recyclable * taxunit),
                                'account_id': li.account_id.id,
                                'analytic_distribution': li.analytic_distribution,
                                'partner_id': self.partner_id.id,
                                'quantity': li.quantity * li.product_id.plastic_weight_non_recyclable,
                            }), (0, 0, {
                                'name': self.name or '/',
                                'credit': abs(li.quantity * li.product_id.plastic_weight_non_recyclable * taxunit),
                                'account_id': self.env.company.plastic_acquirer_account_id.id,
                                'partner_id': self.partner_id.id,
                            })]

    def tax_entry_in_refund(self):
                # Abono del anterior,
                # Solicitud de devolución de impuesto en aduana por Compra de plástico en el extranjero:
                tax_entry = self.plastictax_move_id
                taxproduct = self.env.ref('l10n_es_ipnr_account.aportacion_ipnr_product_template')
                taxline = self.env['account.move.line'].search([('move_id', '=', self.id), ('product_id', '=', taxproduct.id)])
                taxunit = self.env.company.plastic_tax

                #if (taxline.quantity > 0) (cambio 21/01/25):
                if self.plastic_tax:
                    for li in self.invoice_line_ids:
                        if ((li.product_id.ipnr_subject != 'no') and (li.product_id.id) and (li.quantity != 0) and
                                (li.product_id.plastic_weight_non_recyclable != 0) and (li.id != taxline.id)):
                            tax_entry['line_ids'] = [(0, 0, {
                                'product_id': li.product_id.id,
                                'display_type': li.display_type,
                                'name': li.product_id.name,
                                'price_unit': abs(taxunit),
                                'debit': abs(li.quantity * li.product_id.plastic_weight_non_recyclable * taxunit),
                                'account_id': self.env.company.plastic_acquirer_account_id.id,
                                'analytic_distribution': li.analytic_distribution,
                                'partner_id': self.partner_id.id,
                                'quantity': li.quantity * li.product_id.plastic_weight_non_recyclable,
                            }), (0, 0, {
                                'name': self.name or '/',
                                'credit': abs(li.quantity * li.product_id.plastic_weight_non_recyclable * taxunit),
                                'account_id': li.account_id.id,
                                'partner_id': self.partner_id.id,
                            })]

    # Caso 1.- Compramos plástico fuera de España => Impuesto (contemplado)
    # Caso 2.- Compramos plástico dentro de España => Ese plástico ya pagó impuesto (contemplado)
    # Caso 3.- Vendemos en España algo comprado fuera y pagó impuesto => Cobrar al cliente en pvp (contemplado)
    # Caso 4.- Vendemos fuera algo comprado fuera de España => Reclamar impuesto ya pagado (contemplado)
    # Caso 5.- Vendemos fuera algo fabricando por nosotros => No paga impuestos (contemplado en tarifa + constrains)

    @api.constrains('state','plastictax_move_id')
    def _check_plastic_tax_required(self):
        for record in self:
            if (record.move_type in ['in_invoice', 'in_refund']) and (record.state in ['posted']):
                # Control de que el cliente tiene asignado el país y provincia si es en España (por la exclusión Canaria):
                if (not record.picking_partner_id.country_id.id):
                    raise UserError('Pon el país al proveedor para poder controlar el impuesto al plástico: ' + record.picking_partner_id.name)
                if (not record.picking_partner_id.state_id.id) and (record.picking_partner_id.country_id.code == 'ES'):
                    raise UserError('Pon la provincia al proveedor para poder controlar el impuesto al plástico: ' + record.picking_partner_id.name)

                # Si el país es España quien vende ha pagado impuesto y no podemos repercutirlo, si extranjero hemos de pagar:
                if (record.ipnr_tax_zone) and not (record.plastictax_move_id.id):
                    for li in record.invoice_line_ids:
                        if (li.product_id.ipnr_subject != 'no') and (li.product_id.plastic_weight_non_recyclable != 0):
                            message = "El producto " + li.product_id.name + " requiere impuesto al plástico, crea o asigna el apunte correspondiente en esta factura"
                            raise UserError(message)

            if (record.move_type in ['out_invoice', 'out_refund']) and (record.state in ['posted']):
                # Control de que el cliente tiene asignado el país:
                if (not record.picking_partner_id.country_id.id):
                    raise UserError('Pon el país al cliente para poder controlar el impuesto al plástico.')
                if (not record.picking_partner_id.state_id.id) and (record.picking_partner_id.country_id.code == 'ES'):
                    raise UserError('Pon la provincia al cliente para poder controlar el impuesto al plástico: ' + record.picking_partner_id.name)
                # Si es cliente extranjero y el plástico fue importado pagando tasas, podemos recuperar el importe:
                if not (record.ipnr_tax_zone) and not (record.plastictax_move_id.id):
                    for li in record.invoice_line_ids:
                        if ((li.product_id.ipnr_subject != 'no') and (li.product_id.plastic_weight_non_recyclable != 0)
                                and (li.product_id.tax_plastic_type == 'acquirer')):
                            message = "El producto " + li.product_id.name + " es susceptible de recuperar el impuesto al plástico, crea o asigna el apunte correspondiente en esta factura"
                            raise UserError(message)
                # Caso de venta en España de plástico fabricado por nosotros en España, requiere impuesto:
                if (record.ipnr_tax_zone) and not (record.plastictax_move_id.id):
                    for li in record.invoice_line_ids:
                        if ((li.product_id.ipnr_subject != 'no') and (li.product_id.plastic_weight_non_recyclable != 0) and
                                (li.product_id.tax_plastic_type == 'manufacturer')):
                            message = "El producto " + li.product_id.name + " requiere impuesto al plástico, crea o asigna el apunte correspondiente en esta factura"
                            raise UserError(message)
