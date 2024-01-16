from odoo import _, api, fields, models
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'


# PARA TERRITORIO ESPAÑOL, EXCLUIR PROVINCIAS CON CODE = GC y TF, el código del tipo de envío es dropship
    def _get_spain_tax_zone(self):
        taxzone, destination = False, self.picking_partner_id
        if (destination.country_id.code == 'ES') and (destination.state_id.id) and (destination.state_id.code not in ['GC','TF']):
            taxzone = True
        self.spain_tax_zone = taxzone
    spain_tax_zone = fields.Boolean('Spain tax zone', store=False, compute='_get_spain_tax_zone')

    def _get_picking_partner(self):
        destination = self.partner_id
        if (self.move_type in ['out_invoice','out_refund']) and (self.partner_shipping_id.id):
            destination = self.partner_shipping_id
        if (self.move_type in ['in_invoice','in_refund']) and (self.purchase_id.picking_type_id.code == 'dropship'):
            destination = self.purchase_id.dest_address_id
        self.picking_partner_id = destination.id
    picking_partner_id = fields.Many2one('res.partner', string='Picking destination', store=False,
                                             compute='_get_picking_partner')

    pnt_plastictax_move_id = fields.Many2one('account.move', store=True, string='Plastic tax entry', copy=False,
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

    @api.depends('state', 'pnt_plastictax_move_id', 'write_date')
    def _get_show_button_plastic_tax(self):
        show_button = False
        if (self.state not in ['cancel']) and (self.move_type in ['in_invoice','in_refund','out_invoice','out_refund']) and not (self.pnt_plastictax_move_id.id):
            for li in self.invoice_line_ids:
                # Con esta condición verificamos que es plástico:
                if (li.product_id.pnt_plastic_weight != 0) and (li.quantity != 0):
                    # Operaciones de compra fuera de España:
                    if not (self.spain_tax_zone) and (self.move_type in ['in_invoice','in_refund']):
                        show_button = True
                    # Operaciones de venta fuera de España, sólo recuperamos si es comercio (no fabricados):
                    if not (self.spain_tax_zone) and (self.move_type in ['out_invoice','out_refund']) and (li.product_id.pnt_is_manufactured == False):
                        show_button = True
                    # Si vendemos o compramos plástico en España, el impuesto va en PVP o ya lo pagó el proveedor.
                    # Si vendemos en España plástico PRODUCIDO aquí, hemos de pagar (si venta en el extranjero, no):
                    if (self.spain_tax_zone) and (self.move_type in ['out_invoice','out_refund']) and (li.product_id.pnt_is_manufactured):
                        show_button = True
        self.plastic_tax = show_button
    plastic_tax = fields.Boolean('Plastic tax', store=False, compute='_get_show_button_plastic_tax')

    def create_plastic_tax_entry(self):
        # Si es venta o abono de compra: el debe a la 700(producto) y haber a la 475
        # Si es compra o abono de venta: el debe a la 475 y haber a la 600 (depende del producto)
        # Añadir los kg de plástico
        if self.pnt_plastictax_move_id.id:
          raise UserError('Esta factura ya tiene un apunte, modifícalo o quita la asociación.')

        plastic_journal = self.env.company.pnt_plastic_journal_id
        commercial_account = self.env.company.pnt_plastic_commercial_account_id
        manufacture_account = self.env.company.pnt_plastic_manufacture_account_id

        if not (plastic_journal.id) or not (commercial_account.id) or not (manufacture_account.id):
            raise UserError('Asigna el diario y cuentas para el impuesto al plástico en la compañía.')

        ref = "Plastic tax: " + self.partner_id.name
        tax_entry = self.env['account.move'].create(
            {'journal_id': plastic_journal.id, 'move_type': 'entry', 'ref': ref,
             'partner_id': self.partner_id.id, 'invoice_origin': self.invoice_origin})
        self.pnt_plastictax_move_id = tax_entry

        control = 0
        if (self.move_type == 'out_invoice') and (self.spain_tax_zone):
            self.tax_entry_out_invoice_spain()
        if (self.move_type == 'out_invoice') and not (self.spain_tax_zone):
            self.tax_entry_out_invoice_no_spain()

        if (self.move_type == 'out_refund') and (self.spain_tax_zone):
            self.tax_entry_out_refund_spain()
        if (self.move_type == 'out_refund') and not (self.spain_tax_zone):
            self.tax_entry_out_refund_no_spain()

        if (self.move_type == 'in_invoice') and not (self.spain_tax_zone):
            self.tax_entry_in_invoice()
        if (self.move_type == 'in_refund') and not (self.spain_tax_zone):
            self.tax_entry_in_refund()

    def tax_entry_out_invoice_spain(self):
        for li in self.invoice_line_ids:
            if (li.product_id.id) and (li.product_id.pnt_plastic_weight != 0) and (li.quantity != 0):
                # En la venta pagamos impuesto por plástico FABRICADO aquí y vendido aquí:
                if (li.product_id.pnt_is_manufactured):
                    accountpurchase = li.product_id.property_account_expense_id
                    if not accountpurchase.id: accountpurchase = li.product_id.categ_id.property_account_expense_categ_id
                    accountsale = li.product_id.property_account_income_id
                    if not accountsale.id: accountsale = li.product_id.categ_id.property_account_income_categ_id

                    tax_entry = self.pnt_plastictax_move_id
                    tax_entry['line_ids'] = [(0, 0, {
                        'product_id': li.product_id.id,
                        'display_type': li.display_type,
                        'name': li.product_id.name,
                        'price_unit': abs(li.pnt_plastic_tax / li.quantity),
                        'debit': abs(li.pnt_plastic_tax),
                        'account_id': accountsale.id,
                        'analytic_distribution': li.analytic_distribution,
                        'partner_id': self.partner_id.id,
                        'quantity': li.quantity,
                    }), (0, 0, {
                        'name': self.name or '/',
                        'credit': abs(li.pnt_plastic_tax),
                        'account_id': self.env.company.pnt_plastic_manufacture_account_id.id,
                        'partner_id': self.partner_id.id,
                    })]

    def tax_entry_out_invoice_no_spain(self):
        # En la venta reclamamos abono de impuesto pagado si vendemos fabricados IMPORTADOS (que pagamos en aduana anteriormente la tasa):
        for li in self.invoice_line_ids:
            if (li.product_id.id) and (li.product_id.pnt_plastic_weight != 0) and (li.quantity != 0):
                if not (li.product_id.pnt_is_manufactured):
                    accountpurchase = li.product_id.property_account_expense_id
                    if not accountpurchase.id: accountpurchase = li.product_id.categ_id.property_account_expense_categ_id
                    accountsale = li.product_id.property_account_income_id
                    if not accountsale.id: accountsale = li.product_id.categ_id.property_account_income_categ_id

                    tax_entry = self.pnt_plastictax_move_id
                    tax_entry['line_ids'] = [(0, 0, {
                        'product_id': li.product_id.id,
                        'display_type': li.display_type,
                        'name': li.product_id.name,
                        'price_unit': abs(li.pnt_plastic_tax / li.quantity),
                        'credit': abs(li.pnt_plastic_tax),
                        'account_id': accountsale.id,
                        'analytic_distribution': li.analytic_distribution,
                        'partner_id': self.partner_id.id,
                        'quantity': li.quantity,
                    }), (0, 0, {
                        'name': self.name or '/',
                        'debit': abs(li.pnt_plastic_tax),
                        'account_id': self.env.company.pnt_plastic_commercial_account_id.id,
                        'partner_id': self.partner_id.id,
                    })]



    def tax_entry_out_refund_spain(self):
        for li in self.invoice_line_ids:
            if (li.product_id.id) and (li.product_id.pnt_plastic_weight != 0) and (li.quantity != 0):
                # Para venta pagamos impuesto por plástico FABRICADO aquí y vendido aquí, pero no si vuelve a STOCK:
                if (li.product_id.pnt_is_manufactured):
                    accountpurchase = li.product_id.property_account_expense_id
                    if not accountpurchase.id: accountpurchase = li.product_id.categ_id.property_account_expense_categ_id
                    accountsale = li.product_id.property_account_income_id
                    if not accountsale.id: accountsale = li.product_id.categ_id.property_account_income_categ_id

                    tax_entry = self.pnt_plastictax_move_id
                    tax_entry['line_ids'] = [(0, 0, {
                        'product_id': li.product_id.id,
                        'display_type': li.display_type,
                        'name': li.product_id.name,
                        'price_unit': abs(li.pnt_plastic_tax / li.quantity),
                        'debit': abs(li.pnt_plastic_tax),
                        'account_id': self.env.company.pnt_plastic_manufacture_account_id.id,
                        'analytic_distribution': li.analytic_distribution,
                        'partner_id': self.partner_id.id,
                        'quantity': li.quantity,
                    }), (0, 0, {
                        'name': self.name or '/',
                        'credit': abs(li.pnt_plastic_tax),
                        'account_id': accountsale.id,
                        'partner_id': self.partner_id.id,
                    })]

    def tax_entry_out_refund_no_spain(self):
        # En venta si nos han devuelto el impuesto (porque pagamos "no fabricado"
        # hemos de volver a pagarlo ya que introducimos plático en España:
        for li in self.invoice_line_ids:
            if (li.product_id.id) and (li.product_id.pnt_plastic_weight != 0) and (li.quantity != 0):
                if not (li.product_id.pnt_is_manufactured):
                    accountpurchase = li.product_id.property_account_expense_id
                    if not accountpurchase.id: accountpurchase = li.product_id.categ_id.property_account_expense_categ_id
                    accountsale = li.product_id.property_account_income_id
                    if not accountsale.id: accountsale = li.product_id.categ_id.property_account_income_categ_id

                    tax_entry = self.pnt_plastictax_move_id
                    tax_entry['line_ids'] = [(0, 0, {
                        'product_id': li.product_id.id,
                        'display_type': li.display_type,
                        'name': li.product_id.name,
                        'price_unit': abs(li.pnt_plastic_tax / li.quantity),
                        'credit': abs(li.pnt_plastic_tax),
                        'account_id': self.env.company.pnt_plastic_commercial_account_id.id,
                        'analytic_distribution': li.analytic_distribution,
                        'partner_id': self.partner_id.id,
                        'quantity': li.quantity,
                    }), (0, 0, {
                        'name': self.name or '/',
                        'debit': abs(li.pnt_plastic_tax),
                        'account_id': accountsale.id,
                        'partner_id': self.partner_id.id,
                    })]

    def tax_entry_in_invoice(self):
                # Pagamos impuesto en aduana por Compra de plástico en el extranjero (la materia prima no paga, para
                # esto en los productos de materia prima "pnt_plastic_weight" == 0):
                for li in self.invoice_line_ids:
                    if (li.product_id.id) and (li.product_id.pnt_plastic_weight != 0) and (li.quantity != 0):
                        if not (li.product_id.pnt_is_manufactured):
                            accountpurchase = li.product_id.property_account_expense_id
                            if not accountpurchase.id: accountpurchase = li.product_id.categ_id.property_account_expense_categ_id
                            accountsale = li.product_id.property_account_income_id
                            if not accountsale.id: accountsale = li.product_id.categ_id.property_account_income_categ_id

                            tax_entry = self.pnt_plastictax_move_id
                            tax_entry['line_ids'] = [(0, 0, {
                                'product_id': li.product_id.id,
                                'display_type': li.display_type,
                                'name': li.product_id.name,
                                'price_unit': abs(li.pnt_plastic_tax / li.quantity),
                                'debit': abs(li.pnt_plastic_tax),
                                'account_id': accountpurchase.id,
                                'analytic_distribution': li.analytic_distribution,
                                'partner_id': self.partner_id.id,
                                'quantity': li.quantity,
                            }), (0, 0, {
                                'name': self.name or '/',
                                'credit': abs(li.pnt_plastic_tax),
                                'account_id': self.env.company.pnt_plastic_commercial_account_id.id,
                                'partner_id': self.partner_id.id,
                            })]

    def tax_entry_in_refund(self):
                # Abono del anterior:
                # Solicitud de devolución de impuesto en aduana por Compra de plástico en el extranjero,
                # en el caso de devolución:
                for li in self.invoice_line_ids:
                    if (li.product_id.id) and (li.product_id.pnt_plastic_weight != 0) and (li.quantity != 0):
                        if not (li.product_id.pnt_is_manufactured):
                            accountpurchase = li.product_id.property_account_expense_id
                            if not accountpurchase.id: accountpurchase = li.product_id.categ_id.property_account_expense_categ_id
                            accountsale = li.product_id.property_account_income_id
                            if not accountsale.id: accountsale = li.product_id.categ_id.property_account_income_categ_id

                            tax_entry = self.pnt_plastictax_move_id
                            tax_entry['line_ids'] = [(0, 0, {
                                'product_id': li.product_id.id,
                                'display_type': li.display_type,
                                'name': li.product_id.name,
                                'price_unit': abs(li.pnt_plastic_tax / li.quantity),
                                'debit': abs(li.pnt_plastic_tax),
                                'account_id': self.env.company.pnt_plastic_commercial_account_id.id,
                                'analytic_distribution': li.analytic_distribution,
                                'partner_id': self.partner_id.id,
                                'quantity': li.quantity,
                            }), (0, 0, {
                                'name': self.name or '/',
                                'credit': abs(li.pnt_plastic_tax),
                                'account_id': accountpurchase.id,
                                'partner_id': self.partner_id.id,
                            })]


    # Caso 1.- Compramos plástico fuera de España => Impuesto (contemplado)
    # Caso 2.- Compramos plástico dentro de España => Ese plástico ya pagó impuesto (contemplado)
    # Caso 3.- Vendemos en España algo comprado fuera y pagó impuesto => Cobrar al cliente en pvp (contemplado)
    # Caso 4.- Vendemos fuera algo comprado fuera de España => Reclamar impuesto ya pagado (contemplado)
    # Caso 5.- Vendemos fuera algo fabricando por nosotros => No paga impuestos (contemplado en tarifa + constrains)
    @api.constrains('state','pnt_plastictax_move_id')
    def _check_plastic_tax_required(self):
        for record in self:
            if (record.move_type in ['in_invoice', 'in_refund']) and (record.state in ['posted']):
                # Control de que el cliente tiene asignado el país y provincia si es en España (por la exclusión Canaria):
                if (not record.picking_partner_id.country_id.id):
                    raise UserError('Pon el país al proveedor para poder controlar el impuesto al plástico: ' + record.picking_partner_id.name)
                if (not record.picking_partner_id.state_id.id) and (record.picking_partner_id.country_id.code == 'ES'):
                    raise UserError('Pon la provincia al proveedor para poder controlar el impuesto al plástico: ' + record.picking_partner_id.name)

                # Si el país es España quien vende ha pagado impuesto y no podemos repercutirlo, si extranjero hemos de pagar:
                if not (record.spain_tax_zone) and not (record.pnt_plastictax_move_id.id):
                    for li in record.invoice_line_ids:
                        if li.product_id.pnt_plastic_weight != 0:
                            message = "El producto " + li.product_id.name + " requiere impuesto al plástico, crea o asigna el apunte correspondiente en esta factura"
                            raise UserError(message)

            if (record.move_type in ['out_invoice', 'out_refund']) and (record.state in ['posted']):
                # Control de que el cliente tiene asignado el país:
                if (not record.picking_partner_id.country_id.id):
                    raise UserError('Pon el país al cliente para poder controlar el impuesto al plástico.')
                if (not record.picking_partner_id.state_id.id) and (record.picking_partner_id.country_id.code == 'ES'):
                    raise UserError('Pon la provincia al cliente para poder controlar el impuesto al plástico: ' + record.picking_partner_id.name)
                # Si es cliente extranjero y el plástico fue importado pagando tasas, podemos recuperar el importe:
                if not (record.spain_tax_zone) and not (record.pnt_plastictax_move_id.id):
                    for li in record.invoice_line_ids:
                        if (li.product_id.pnt_plastic_weight != 0) and (li.product_id.categ_id.pnt_is_manufactured == False):
                            message = "El producto " + li.product_id.name + " es susceptible de recuperar el impuesto al plástico, crea o asigna el apunte correspondiente en esta factura"
                            raise UserError(message)
                # Caso de venta en España de plástico fabricado por nosotros en España, requiere impuesto:
                if (record.spain_tax_zone) and not (record.pnt_plastictax_move_id.id):
                    for li in record.invoice_line_ids:
                        if (li.product_id.pnt_plastic_weight != 0) and (li.product_id.categ_id.pnt_is_manufactured == True):
                            message = "El producto " + li.product_id.name + " requiere impuesto al plástico, crea o asigna el apunte correspondiente en esta factura"
                            raise UserError(message)
