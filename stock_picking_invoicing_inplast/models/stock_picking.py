# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_mark_and_invoice(self):
        """Marca los albaranes seleccionados como 'Para Facturar' y genera
        facturas borrador en un único paso.

        Requisitos por albarán:
          - Estado 'done' (validado).
          - invoice_state distinto de 'invoiced' (no facturado ya).

        Lógica:
          1. Marca todos los válidos como '2binvoiced'.
          2. Instancia el wizard stock.invoice.onshipping con esos albaranes.
          3. Genera las facturas borrador y actualiza invoice_state a 'invoiced'.
          4. Redirige a la vista de las facturas creadas.
        """
        to_process = self.filtered(
            lambda p: p.state == "done" and p.invoice_state != "invoiced"
        )

        skipped = len(self) - len(to_process)
        if not to_process:
            raise UserError(
                _(
                    "No hay albaranes válidos en la selección.\n"
                    "Deben estar en estado 'Hecho' y no haber sido facturados todavía."
                )
            )

        # Paso 1: marcar como para facturar (idempotente si ya lo estaban)
        to_process.set_to_be_invoiced()

        # Paso 2: instanciar el wizard reutilizando toda su lógica
        wizard = (
            self.env["stock.invoice.onshipping"]
            .with_context(
                active_ids=to_process.ids,
                active_model=self._name,
            )
            .create(
                {
                    "group": "picking",
                    "invoice_date": fields.Date.today(),
                }
            )
        )

        # Paso 3: generar facturas y actualizar estado
        invoices = wizard._action_generate_invoices()
        if invoices:
            wizard._update_picking_invoice_status(invoices.mapped("picking_ids"))

        if not invoices:
            raise UserError(
                _(
                    "No se han podido generar facturas.\n"
                    "Comprueba que los albaranes tienen líneas de movimiento "
                    "y un diario contable configurado."
                )
            )

        # Paso 4: redirigir a las facturas creadas
        inv_types = invoices.mapped("move_type")
        if any(t in ("out_invoice", "out_refund") for t in inv_types):
            xmlid = "account.action_move_out_invoice_type"
        else:
            xmlid = "account.action_move_in_invoice_type"

        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        action["domain"] = [("id", 'in', invoices.ids)]
        action["name"] = _("Facturas borrador (%d)") % len(invoices)

        if skipped:
            # El mensaje de aviso se muestra vía notificación en el cliente
            action.setdefault("context", {})
            action["context"]["skipped_pickings"] = skipped

        if len(invoices) == 1:
            action["views"] = [
                (self.env.ref("account.view_move_form").id, "form")
            ]
            action["res_id"] = invoices.id

        return action
