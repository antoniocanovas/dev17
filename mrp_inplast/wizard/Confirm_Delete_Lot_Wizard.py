from odoo import _, api, fields, models
from odoo.exceptions import UserError

class ConfirmDeleteLotWizard(models.TransientModel):
    _name = 'confirm.delete.lot.wizard'
    _description = 'Confirm Delete Lot Wizard'

    lot_names = fields.Char(string="Lotes a eliminar", readonly=True)

    def confirm_delete(self):
        """ Este método se ejecuta cuando se confirma la eliminación de un lote. """
        active_id = self.env.context.get('active_id')
        wizard = self.env['pallet.boxes.wizard'].browse(active_id)
        if not wizard or not wizard.pnt_barcode_input:
            raise UserError(_("No se encontró el asistente o el campo de entrada está vacío."))

        lot_names = wizard.pnt_barcode_input.split('MO')
        lot_names = [lot_name.strip() for lot_name in lot_names if lot_name.strip()]

        for lot_name in lot_names:
            lot_name_full = 'MO' + lot_name
            lot_to_remove = self.env['stock.lot'].search([('name', '=', lot_name_full), ('parent_id', '=', wizard.pallet_id.id)])
            if lot_to_remove:
                lot_to_remove.unlink()
            else:
                raise UserError(_("El lote '%s' no fue encontrado o ya ha sido eliminado.") % lot_name_full)

        # Limpiar el campo de entrada en el asistente original
        wizard.pnt_barcode_input = ''

        # Actualizar la lista de códigos de barras procesados
        if wizard.pallet_id:
            lots = self.env['stock.lot'].search([('parent_id', '=', wizard.pallet_id.id)])
            wizard.pnt_processed_barcodes = [(6, 0, lots.ids)]

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pallet.boxes.wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new',
        }
