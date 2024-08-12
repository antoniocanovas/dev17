from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ConfirmDeleteLotWizard(models.TransientModel):
    _name = 'confirm.delete.lot.wizard'
    _description = 'Confirm Delete Lot Wizard'

    lot_names = fields.Char(string="Lots to Delete", readonly=True)

    def confirm_delete(self):
        """ This method is executed when the user confirms the deletion of a lot. """
        active_id = self.env.context.get('active_id')
        wizard = self.env['pallet.boxes.wizard'].browse(active_id)
        if not wizard:
            raise UserError(_("No pallet wizard found."))

        lot_names = self.lot_names.split(',')
        lot_names = [lot_name.strip() for lot_name in lot_names if lot_name.strip()]

        non_existing_lots = []
        for lot_name in lot_names:
            lot_to_remove = self.env['stock.lot'].search([
                ('name', '=', lot_name),
                ('parent_id', '=', wizard.pallet_id.id)
            ], limit=1)
            if lot_to_remove:
                lot_to_remove.unlink()
            else:
                non_existing_lots.append(lot_name)

        # Clear the barcode input field in the original wizard
        wizard.pnt_barcode_input = ''

        # Update the processed barcodes list
        if wizard.pallet_id:
            lots = self.env['stock.lot'].search([('parent_id', '=', wizard.pallet_id.id)])
            wizard.pnt_processed_barcodes = [(6, 0, lots.ids)]

        # Prepare the notification message and refresh the wizard view
        if non_existing_lots:
            non_existing_message = ', '.join(non_existing_lots)
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'pallet.boxes.wizard',
                'view_mode': 'form',
                'res_id': wizard.id,
                'target': 'new',
                'context': self.env.context,
                "flags": {'form': {'action_buttons': True}},
                "notification": {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": _("Lots Deletion Summary"),
                        "message": _("Some lots could not be deleted because they do not exist for this pallet: [%s]") % non_existing_message,
                        "sticky": False,
                        "type": "warning",
                    },
                },
            }

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pallet.boxes.wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new',
            'context': self.env.context,
            "flags": {'form': {'action_buttons': True}},
            "notification": {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Lots Deleted"),
                    "message": _("Selected lots have been successfully deleted."),
                    "sticky": False,
                    "type": "success",
                },
            },
        }
