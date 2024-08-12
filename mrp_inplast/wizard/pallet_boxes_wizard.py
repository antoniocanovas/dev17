from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PalletBoxesWizard(models.TransientModel):
    _name = 'pallet.boxes.wizard'
    _description = 'Add boxes to Lot'

    production_id = fields.Many2one(
        'mrp.production', required=True,
        default=lambda self: self.env.context.get('production_id', None))
    lot_producing_id = fields.Many2one(related="production_id.lot_producing_id")
    pallet_id = fields.Many2one('stock.lot', string="Pallet", domain="[('parent_id', '=', lot_producing_id)]")
    pnt_barcode_input = fields.Text('Boxes read')
    pnt_processed_barcodes = fields.Many2many('stock.lot', string="Boxes")
    processed_count = fields.Integer(
        string="Processed Count", compute='_compute_counts', store=True)
    remaining_count = fields.Integer(
        string="Remaining to 24", compute='_compute_counts', store=True)
    show_confirmation = fields.Boolean(default=False)

    @api.depends('pnt_processed_barcodes')
    def _compute_counts(self):
        for record in self:
            record.processed_count = len(record.pnt_processed_barcodes)
            record.remaining_count = max(0, 24 - record.processed_count)

    @api.onchange('pallet_id')
    def _onchange_pallet_id(self):
        """ This method executes when the 'pallet_id' field changes. """
        if self.pallet_id:
            lots = self.env['stock.lot'].search([('parent_id', '=', self.pallet_id.id)])
            self.pnt_processed_barcodes = [(6, 0, lots.ids)]
            self.pnt_barcode_input = ''
        else:
            self.pnt_processed_barcodes = [(5, 0, 0)]

    def _process_barcode_input(self):
        max_boxes = 24  # Limit for the number of boxes

        for record in self:
            if not record.pnt_barcode_input:
                continue  # Skip if no input

            # Process barcode input
            line = record.pnt_barcode_input
            lots_to_process = line.split('MO')
            lots_to_process = [lot.strip() for lot in lots_to_process if lot.strip()]

            if not lots_to_process:
                continue  # Skip if no valid lot names

            # Find the subproduct
            subproduct = self.env['product.product'].search([
                ('pnt_product_type', '=', 'box'),
                ('id', 'in', record.production_id.product_id.pnt_parent_id.pnt_packing_ids.ids)
            ], limit=1)

            if not subproduct:
                raise UserError(_("No subproduct with type 'box' was found."))

            existing_lots = self.env['stock.lot'].search([('parent_id', '=', record.pallet_id.id)])
            existing_lots_count = len(existing_lots)

            # Calculate the total boxes if adding the new ones
            if existing_lots_count + len(lots_to_process) > max_boxes:
                # Show error notification
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": _("Error"),
                        "message": _("You have exceeded 24 boxes. No new lots were created."),
                        "sticky": False,
                        "type": "danger",
                    },
                }

            # Try block to handle barcode processing and field updates
            try:
                for lot in lots_to_process:
                    lot_name = 'MO' + lot
                    exist = self.env['stock.lot'].search([('name', '=', lot_name)])
                    if not exist:
                        new_lot = self.env['stock.lot'].create({
                            'product_id': subproduct.id,
                            'name': lot_name,
                            'parent_id': record.pallet_id.id,
                        })
                    # Update processed barcodes even if the lot exists
                    lots = self.env['stock.lot'].search([('parent_id', '=', record.pallet_id.id)])
                    record.pnt_processed_barcodes = [(6, 0, lots.ids)]
            except Exception as e:
                raise UserError(_("Error processing barcodes: %s") % str(e))

            # Update related boxes on the pallet
            if record.pallet_id:
                record.pallet_id.related_boxes_ids = [(6, 0, record.pnt_processed_barcodes.ids)]

    def _process_lot_removal(self):
        """ Processes lot removal and handles notifications """
        if not self.pnt_barcode_input:
            raise UserError(_("Please enter a lot name to remove."))

        lot_names = self.pnt_barcode_input.split('MO')
        lot_names = [lot_name.strip() for lot_name in lot_names if lot_name.strip()]

        if not lot_names:
            raise UserError(_("Please enter at least one valid lot name."))

        not_found_lots = []
        removed_lots = []

        for lot_name in lot_names:
            lot_name_full = 'MO' + lot_name
            lot_to_remove = self.env['stock.lot'].search(
                [('name', '=', lot_name_full), ('parent_id', '=', self.pallet_id.id)])
            if lot_to_remove:
                lot_to_remove.unlink()
                removed_lots.append(lot_name_full)
            else:
                not_found_lots.append(lot_name_full)

        # Update pnt_barcode_input with the lots that were not found
        if not_found_lots:
            self.pnt_barcode_input = ', '.join(not_found_lots)
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Lots Not Found"),
                    "message": _("The following lots were not removed because they do not exist: %s") % ', '.join(
                        not_found_lots),
                    "sticky": False,
                    "type": "warning",
                },
            }

        # Update the processed barcodes list
        if self.pallet_id:
            lots = self.env['stock.lot'].search([('parent_id', '=', self.pallet_id.id)])
            self.pnt_processed_barcodes = [(6, 0, lots.ids)]

    def trigger_remove_lot(self):
        """ Trigger removal confirmation """
        self.show_confirmation = True
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pallet.boxes.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def confirm_remove_lot(self):
        """ Executed when the "Yes" button is clicked. """
        try:
            action = self._process_lot_removal()
            if action:
                return action
        except UserError as e:
            # Handle error and update the wizard to its original state
            self._onchange_pallet_id()
            self.show_confirmation = False
            # Return action to display the error notification
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Error"),
                    "message": str(e),
                    "sticky": False,
                    "type": "danger",
                },
            }
        else:
            # Ensure to hide the confirmation dialog and update fields
            self.show_confirmation = False
            # Return action to refresh the wizard view
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'pallet.boxes.wizard',
                'view_mode': 'form',
                'res_id': self.id,
                'target': 'new',
            }

    def cancel_remove_lot(self):
        """ Executed when the "No" button is clicked. """
        self.show_confirmation = False
        self._onchange_pallet_id()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pallet.boxes.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def add_lots(self):
        action = self._process_barcode_input()
        if action:
            return action
        self._onchange_pallet_id()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pallet.boxes.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
