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

    @api.depends('pnt_processed_barcodes')
    def _compute_counts(self):
        for record in self:
            record.processed_count = len(record.pnt_processed_barcodes)
            record.remaining_count = max(0, 24 - record.processed_count)

    @api.onchange('pallet_id')
    def _onchange_pallet_id(self):
        """ Este método se ejecuta cuando cambia el campo 'pallet_id'. """
        if self.pallet_id:
            lots = self.env['stock.lot'].search([('parent_id', '=', self.pallet_id.id)])
            self.pnt_processed_barcodes = [(6, 0, lots.ids)]
            self.pnt_barcode_input = ''
        else:
            self.pnt_processed_barcodes = [(5, 0, 0)]

    def _process_barcode_input(self):
        max_boxes = 24  # Limit for the number of boxes
        unprocessed_lots = []

        for record in self:
            if not record.pnt_barcode_input:
                continue  # Skip if no input

            line = record.pnt_barcode_input
            lots_to_process = line.split('MO')
            lots_to_process = [lot.strip() for lot in lots_to_process if lot.strip()]

            if not lots_to_process:
                continue  # Skip if no valid lot names

            # Debug: Check the lots to process
            print("Lots to process:", lots_to_process)

            subproduct = self.env['product.product'].search([
                ('pnt_product_type', '=', 'box'),
                ('id', 'in', record.production_id.product_id.pnt_parent_id.pnt_packing_ids.ids)
            ], limit=1)

            if not subproduct:
                raise UserError(_("No se encontró un subproducto con el tipo 'box'."))

            existing_lots = self.env['stock.lot'].search([('parent_id', '=', record.pallet_id.id)])
            existing_lots_count = len(existing_lots)

            # Check if total exceeds max_boxes
            if existing_lots_count + len(lots_to_process) > max_boxes:
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": _("Maximum Number of Boxes Exceeded"),
                        "message": _("You have exceeded the limit of 24 boxes. No lots were created."),
                        "sticky": False,
                        "type": "warning",
                    },
                }

            created_lots_count = 0

            # Try block to handle barcode processing and field updates
            try:
                for lot in lots_to_process:
                    lot_name = 'MO' + lot
                    exist = self.env['stock.lot'].search([('name', '=', lot_name)])
                    if record.pallet_id:
                        record.pallet_id.related_boxes_ids = [(6, 0, record.pnt_processed_barcodes.ids)]
                    if not exist:
                        new_lot = self.env['stock.lot'].create({
                            'product_id': subproduct.id,
                            'name': lot_name,
                            'parent_id': record.pallet_id.id,
                        })
                        created_lots_count += 1
                    # Update processed barcodes even if the lot exists
                    lots = self.env['stock.lot'].search([('parent_id', '=', record.pallet_id.id)])
                    record.pnt_processed_barcodes = [(6, 0, lots.ids)]
            except Exception as e:
                print("Error processing barcodes:", str(e))  # Log the error

            # Update related boxes on the pallet
            if record.pallet_id:
                record.pallet_id.related_boxes_ids = [(6, 0, record.pnt_processed_barcodes.ids)]

        # Handle unprocessed lots after processing
        if unprocessed_lots:
            unprocessed_message = ', '.join(unprocessed_lots)
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Some Lots Could Not Be Created"),
                    "message": _("The following lots could not be created: %s") % unprocessed_message,
                    "sticky": False,
                    "type": "warning",
                },
            }

    def add_lots(self):
        action = self._process_barcode_input()
        if action:
            self._onchange_pallet_id()
            return action
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pallet.boxes.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def remove_lot(self):
        """ Este método se ejecuta cuando se hace clic en el botón "Remove Selected Lot". """
        if not self.pnt_barcode_input:
            raise UserError(_("Por favor, ingrese un nombre de lote para eliminar."))

        lot_names = self.pnt_barcode_input.split('MO')
        lot_names = [lot_name.strip() for lot_name in lot_names if lot_name.strip()]

        if not lot_names:
            raise UserError(_("Por favor, ingrese al menos un nombre de lote válido."))

        lot_names_str = ', '.join(['MO' + name for name in lot_names])

        return {
            'type': 'ir.actions.act_window',
            'name': 'Confirm Delete Lot',
            'res_model': 'confirm.delete.lot.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lot_names': lot_names_str,
                'active_id': self.id,
            },
        }
