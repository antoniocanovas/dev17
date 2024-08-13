from odoo import _, api, fields, models
from odoo.exceptions import UserError

# Define un modelo transitorio para manejar operaciones relacionadas con la adición y eliminación de cajas (lotes) a/de un palé
class PalletBoxesWizard(models.TransientModel):
    _name = 'pallet.boxes.wizard'
    _description = 'Add boxes to Lot'

    # Define campos para el asistente, incluyendo relaciones, entradas y valores computados

    # Referencia a la orden de producción de manufactura, requerida para vincular este asistente a un contexto de producción específico
    production_id = fields.Many2one(
        'mrp.production', required=True,
        default=lambda self: self.env.context.get('production_id', None)
    )
    # Un campo relacionado que automáticamente obtiene el lote que se está produciendo de la orden de producción vinculada
    lot_producing_id = fields.Many2one(related="production_id.lot_producing_id")
    # El palé seleccionado para agregar o eliminar cajas, con un dominio para filtrar solo palés relacionados con el lote de producción
    pallet_id = fields.Many2one('stock.lot', string="Pallet", domain="[('parent_id', '=', lot_producing_id)]")
    # Entrada de texto para ingresar datos de códigos de barras de las cajas a procesar
    pnt_barcode_input = fields.Text('Boxes read')
    # Una relación many2many que almacena todos los lotes de cajas que han sido procesados y están asociados con el palé seleccionado
    pnt_processed_barcodes = fields.Many2many('stock.lot', string="Boxes")
    # Contador de cuántas cajas han sido procesadas, campo computado basado en pnt_processed_barcodes
    processed_count = fields.Integer(
        string="Processed Count", compute='_compute_counts', store=True
    )
    # Campo computado que muestra cuántas cajas más se pueden agregar para alcanzar un total de 24
    remaining_count = fields.Integer(
        string="Remaining to 24", compute='_compute_counts', store=True
    )
    # Un campo booleano para activar el cuadro de diálogo de confirmación al eliminar lotes
    show_confirmation = fields.Boolean(default=False)

    # Método para computar el número de cajas procesadas y restantes
    @api.depends('pnt_processed_barcodes')
    def _compute_counts(self):
        # Recorre cada registro en el modelo transitorio
        for record in self:
            # Establece el conteo procesado como la longitud de la lista de códigos de barras procesados
            record.processed_count = len(record.pnt_processed_barcodes)
            # Calcula el conteo restante necesario para alcanzar 24 cajas
            record.remaining_count = max(0, 24 - record.processed_count)

    # Método onchange para ejecutar lógica cuando el campo pallet_id cambia
    @api.onchange('pallet_id')
    def _onchange_pallet_id(self):
        """Ejecutado cuando el campo 'pallet_id' cambia."""
        if self.pallet_id:
            # Busca lotes que tengan el palé actual como su padre y los establece como códigos de barras procesados
            lots = self.env['stock.lot'].search([('parent_id', '=', self.pallet_id.id)])
            self.pnt_processed_barcodes = [(6, 0, lots.ids)]
            # Limpia el campo de entrada de códigos de barras
            self.pnt_barcode_input = ''
        else:
            # Si no se selecciona un palé, limpia los códigos de barras procesados
            self.pnt_processed_barcodes = [(5, 0, 0)]

    # Método para procesar la entrada del campo de código de barras y actualizar los registros en consecuencia
    def _process_barcode_input(self):
        # Establece el número máximo de cajas permitidas
        max_boxes = 24

        # Itera sobre cada registro del asistente
        for record in self:
            # Continúa al siguiente registro si no hay entrada de código de barras
            if not record.pnt_barcode_input:
                continue

            # Divide la entrada por 'MO' para obtener identificadores individuales de lotes y limpiarlos
            line = record.pnt_barcode_input
            lots_to_process = line.split('MO')
            lots_to_process = [lot.strip() for lot in lots_to_process if lot.strip()]

            # Salta si no hay lotes válidos para procesar
            if not lots_to_process:
                continue

            # Busca el subproducto con tipo 'box' relacionado con la producción actual
            subproduct = self.env['product.product'].search([
                ('pnt_product_type', '=', 'box'),
                ('id', 'in', record.production_id.product_id.pnt_parent_id.pnt_packing_ids.ids)
            ], limit=1)

            # Lanza un error si no se encuentra subproducto
            if not subproduct:
                raise UserError(_("No subproduct with type 'box' was found."))

            # Obtiene todos los lotes asociados con el palé actual
            existing_lots = self.env['stock.lot'].search([('parent_id', '=', record.pallet_id.id)])
            existing_lots_count = len(existing_lots)

            # Verifica si agregar los nuevos lotes excede el límite máximo
            if existing_lots_count + len(lots_to_process) > max_boxes:
                # Devuelve una notificación si se excede el límite
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

            # Maneja excepciones que pueden ocurrir durante el procesamiento de códigos de barras
            try:
                for lot in lots_to_process:
                    # Construye el nombre completo del lote
                    lot_name = 'MO' + lot
                    # Verifica si el lote ya existe
                    exist = self.env['stock.lot'].search([('name', '=', lot_name)])
                    if not exist:
                        # Crea un nuevo lote si no existe
                        new_lot = self.env['stock.lot'].create({
                            'product_id': subproduct.id,
                            'name': lot_name,
                            'parent_id': record.pallet_id.id,
                        })
                    # Actualiza los códigos de barras procesados con todos los lotes relacionados con el palé actual
                    lots = self.env['stock.lot'].search([('parent_id', '=', record.pallet_id.id)])
                    record.pnt_processed_barcodes = [(6, 0, lots.ids)]
            except Exception as e:
                # Lanza un error si hay una excepción
                raise UserError(_("Error processing barcodes: %s") % str(e))

            # Actualiza las cajas relacionadas en el palé, si aplica
            if record.pallet_id:
                record.pallet_id.related_boxes_ids = [(6, 0, record.pnt_processed_barcodes.ids)]

    # Método para manejar la eliminación de lotes basado en el campo de entrada de código de barras
    def _process_lot_removal(self):
        """Procesa la eliminación de lotes y maneja las notificaciones."""
        # Lanza un error si no se proporciona entrada de código de barras
        if not self.pnt_barcode_input:
            raise UserError(_("Please enter a lot name to remove."))

        # Extrae nombres de lotes de la entrada
        lot_names = self.pnt_barcode_input.split('MO')
        lot_names = [lot_name.strip() for lot_name in lot_names if lot_name.strip()]

        # Lanza un error si no se encuentran nombres de lotes válidos
        if not lot_names:
            raise UserError(_("Please enter at least one valid lot name."))

        # Listas para rastrear lotes que se eliminan o no se encuentran
        not_found_lots = []
        removed_lots = []

        # Itera sobre los nombres de lotes para eliminarlos
        for lot_name in lot_names:
            # Construye el nombre completo del lote
            lot_name_full = 'MO' + lot_name
            # Busca el lote para eliminar
            lot_to_remove = self.env['stock.lot'].search(
                [('name', '=', lot_name_full), ('parent_id', '=', self.pallet_id.id)]
            )
            if lot_to_remove:
                # Elimina el lote si existe
                lot_to_remove.unlink()
                removed_lots.append(lot_name_full)
            else:
                # Agrega a la lista de no encontrados si no existe
                not_found_lots.append(lot_name_full)

        # Si hay lotes no encontrados, actualiza la entrada y muestra una notificación de advertencia
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

        # Actualiza la lista de códigos de barras procesados después de la eliminación
        if self.pallet_id:
            lots = self.env['stock.lot'].search([('parent_id', '=', self.pallet_id.id)])
            self.pnt_processed_barcodes = [(6, 0, lots.ids)]

    # Método para activar el proceso de eliminación de lotes y mostrar un cuadro de diálogo de confirmación
    def trigger_remove_lot(self):
        """Activa la confirmación de eliminación."""
        # Establece la bandera de confirmación en verdadero
        self.show_confirmation = True
        # Devuelve una acción para abrir el asistente en una nueva ventana
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pallet.boxes.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    # Confirma y ejecuta la eliminación de lotes cuando se acepta la confirmación
    def confirm_remove_lot(self):
        """Ejecutado cuando se hace clic en el botón "Sí"."""
        try:
            # Procesa la eliminación de lotes
            action = self._process_lot_removal()
            if action:
                return action
        except UserError as e:
            # Maneja cualquier error durante la eliminación de lotes, restablece el estado del asistente
            self._onchange_pallet_id()
            self.show_confirmation = False
            # Devuelve acción para mostrar la notificación de error
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
            # Oculta el cuadro de diálogo de confirmación y actualiza la vista del asistente
            self.show_confirmation = False
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'pallet.boxes.wizard',
                'view_mode': 'form',
                'res_id': self.id,
                'target': 'new',
            }

    # Cancela el proceso de eliminación y revierte cualquier cambio cuando se rechaza la confirmación
    def cancel_remove_lot(self):
        """Ejecutado cuando se hace clic en el botón "No"."""
        # Restablece la bandera de confirmación y restablece el estado del asistente
        self.show_confirmation = False
        self._onchange_pallet_id()
        # Devuelve una acción para abrir el asistente en una nueva ventana
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pallet.boxes.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    # Método para manejar la adición de lotes al palé utilizando la entrada de código de barras
    def add_lots(self):
        # Procesa la entrada de código de barras para agregar lotes
        action = self._process_barcode_input()
        if action:
            return action
        # Restablece el estado del asistente
        self._onchange_pallet_id()
        # Devuelve una acción para actualizar la vista del asistente
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pallet.boxes.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
