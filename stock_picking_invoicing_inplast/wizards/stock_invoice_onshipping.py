# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
#
# Correcciones sobre stock_picking_invoicing (OCA) para el caso de dropshipping.
#
# El módulo OCA no tiene entrada en INVOICE_TYPE_MAP para el caso
# (incoming, supplier, customer) — envío directo de proveedor a cliente —
# y además deriva el tipo de diario mirando solo el origen del picking,
# lo que hace que un albarán de dropshipping obtenga diario de COMPRA en lugar
# de VENTA.
#
# Fixes aplicados:
#   _get_invoice_type → devuelve "out_invoice" explícitamente para dropshipping.
#   _get_journal_type → devuelve "sale" para dropshipping.

from odoo import api, fields, models


def _is_dropship(picking):
    """True si el albarán es de tipo dropshipping: incoming de proveedor a cliente."""
    if not picking.exists() or not picking.move_ids:
        return False
    line = fields.first(picking.move_ids)
    return (
        picking.picking_type_id.code == "incoming"
        and line.location_id.usage == "supplier"
        and line.location_dest_id.usage == "customer"
    )


class StockInvoiceOnshipping(models.TransientModel):
    _inherit = "stock.invoice.onshipping"

    @api.model
    def _get_journal_type(self):
        active_ids = self.env.context.get("active_ids", [])
        if active_ids:
            picking = self.env["stock.picking"].browse(active_ids[0])
            if _is_dropship(picking):
                return "sale"
        return super()._get_journal_type()

    def _get_invoice_type(self):
        active_ids = self.env.context.get("active_ids", [])
        if active_ids:
            picking = self.env["stock.picking"].browse(active_ids[0])
            if _is_dropship(picking):
                return "out_invoice"
        return super()._get_invoice_type()
