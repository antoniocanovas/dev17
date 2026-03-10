from odoo import models, fields, api, _
from odoo.exceptions import UserError
from gtin import GTIN


class StockLot(models.Model):
    _inherit = "stock.lot"

    # Computed field to dynamically calculate product_id
    box_product_id = fields.Many2one(
        "product.product", compute="_compute_box_product_id", string="Box Product"
    )

    mrp_production_id = fields.Many2one(
        "mrp.production",  # Add this line to specify the comodel
        string="mrp production",
        compute="_compute_mrp_production_id",
    )

    def _compute_mrp_production_id(self) -> None:
        for record in self:
            production = self.env["mrp.production"].search_read(
                [("lot_producing_id", "=", record.parent_id.id)], ["id"], limit=1
            )
            record["mrp_production_id"] = (
                production[0]["id"] if production else False
            )

    # Campo Many2many para las cajas relacionadas
    related_boxes_ids = fields.Many2many(
        "stock.lot",
        "stock_lot_related_boxes_rel",  # Explicit name for the relation table
        "lot_id",  # Column name for the current model (source)
        "related_lot_id",  # Column name for the target model
        string="Related Boxes",
        help="Boxes related to this lot.",
        domain="[('product_id', '=', box_product_id), ('parent_id', '=', id)]",
    )
    invisible_fields = fields.Boolean(
        string="Invisible Fields",
    )
    # sscc = fields.Char(string="SSCC1", help="SSCC1 number for the lot")
    # sscc2 = fields.Char(string="SSCC2", help="SSCC2 number for the lot")

    sscc_code_ids = fields.One2many("pnt.sscc.code", "lot_id", string="SSCC Codes")

    def get_next_sscc(self, qty: int = 1) -> None:
        """
        Genera códigos SSCC-18 para el lote actual.

        Estructura SSCC-18 (18 dígitos):
        - 1 dígito: Extension digit
        - 16 dígitos: GS1 Company Prefix + Serial Reference
        - 1 dígito: Check digit (calculado)

        :param qty: Cantidad de códigos SSCC a generar
        """
        # Buscar la secuencia SSCC configurada
        seq = self.env["ir.sequence"].search([("code", "=", "pnt.sscc.code")], limit=1)

        if not seq:
            raise UserError(
                "Error de configuración:\n\n"
                "No se encontró la secuencia SSCC (código: pnt.sscc.code).\n"
                "Por favor, verifica la configuración del módulo."
            )

        # Validar que existe el extension digit
        pnt_extension_digit = seq.pnt_extension_digit
        if pnt_extension_digit is False or pnt_extension_digit is None:
            raise UserError(
                "Error de configuración SSCC:\n\n"
                "El dígito de extensión (Extension Digit) no está configurado.\n"
                "Por favor, configura este campo en la secuencia SSCC."
            )

        # Validar que el extension digit es un solo dígito (0-9)
        if not (0 <= pnt_extension_digit <= 9):
            raise UserError(
                "Error de configuración SSCC:\n\n"
                "El dígito de extensión debe ser un número entre 0 y 9.\n"
                f"Valor actual: {pnt_extension_digit}"
            )

        # Validar que existen prefix y padding
        if not seq.prefix:
            raise UserError(
                "Error de configuración SSCC:\n\n"
                "El prefijo (Prefix) no está configurado.\n"
                "Por favor, configura el prefijo de empresa en la secuencia SSCC."
            )

        if not seq.padding or seq.padding < 1:
            raise UserError(
                "Error de configuración SSCC:\n\n"
                "El padding no está configurado o es menor a 1.\n"
                "Por favor, configura un padding válido en la secuencia SSCC."
            )

        # Validar que prefix + padding = 16 dígitos
        prefix_length = len(seq.prefix)
        total_length = prefix_length + seq.padding

        if total_length != 16:
            raise UserError(
                "Error de configuración SSCC:\n\n"
                "Para generar un código SSCC-18 válido, la suma de:\n"
                f"  • Longitud del prefijo ({prefix_length} dígitos)\n"
                f"  • Padding ({seq.padding} dígitos)\n\n"
                "Debe ser igual a 16 dígitos.\n\n"
                f"Total actual: {total_length} dígitos\n"
                "Requerido: 16 dígitos\n\n"
                "Por favor, ajusta la configuración en:\n"
                "Inventario > Configuración > SSCC Sequence"
            )

        # Generar los códigos SSCC
        for _i in range(qty):
            try:
                # Generar el siguiente número de secuencia (ya incluye prefix + número
                # con padding)
                # Ejemplo: si prefix="8412345" y padding=9, devuelve "8412345000000001"
                # (16 dígitos)
                serial_reference = self.env["ir.sequence"].next_by_code("pnt.sscc.code")

                if not serial_reference:
                    raise UserError(
                        "Error al generar SSCC:\n\n"
                        "No se pudo obtener el siguiente número de la secuencia.\n"
                        "Por favor, verifica la configuración de la secuencia SSCC."
                    )

                # Validar que el número generado tiene exactamente 16 dígitos
                if len(serial_reference) != 16:
                    raise UserError(
                        "Error al generar SSCC:\n\n"
                        f"El número de secuencia generado tiene {len(serial_reference)}"
                        f" dígitos.\n"
                        "Se esperaban 16 dígitos.\n\n"
                        "Verifica la configuración de prefix y padding en la secuencia"
                        " SSCC."
                    )

                # Construir los primeros 17 dígitos: extension_digit (1) +
                # serial_reference (16)
                sscc_without_check = str(pnt_extension_digit) + serial_reference

                # Calcular el dígito de control sobre los 17 dígitos
                check_digit = GTIN(raw=sscc_without_check).check_digit

                # Construir el SSCC-18 completo (18 dígitos)
                sscc_18 = sscc_without_check + str(check_digit)

                # Validar que el SSCC final tiene 18 dígitos
                if len(sscc_18) != 18:
                    raise UserError(
                        f"Error interno al generar SSCC:\n\n"
                        f"El código SSCC generado tiene {len(sscc_18)} dígitos.\n"
                        "Se esperaban 18 dígitos.\n\n"
                        "Por favor, contacta al administrador del sistema."
                    )

                # Crear el registro del código SSCC
                sscc_object = self.env["pnt.sscc.code"].create(
                    {
                        "name": sscc_18,
                        "lot_id": self.id,
                    }
                )

                if sscc_object:
                    self.sscc_code_ids = [(4, sscc_object.id)]

            except Exception as e:
                # Capturar cualquier error y mostrarlo de forma amigable
                if isinstance(e, UserError):
                    raise
                else:
                    raise UserError(
                        f"Error al generar código SSCC:\n\n"
                        f"{str(e)}\n\n"
                        "Por favor, verifica la configuración de la secuencia SSCC."
                    ) from e

    @api.depends("product_id")
    def _compute_box_product_id(self) -> None:
        for record in self:
            invisible_fields = True
            if record.product_id:
                matching_record = None
                for packing_record in record.product_id.pnt_parent_id.pnt_packing_ids:
                    pallet_qty = record.product_id.pnt_parent_qty
                    box_qty = record.product_id.pnt_box_qty
                    division = pallet_qty // box_qty
                    check_qty = packing_record.pnt_parent_qty
                    # Salir del bucle si se cumple la condición
                    if division == check_qty:
                        matching_record = packing_record
                        break
                # Find the box product related to this lot's product
                if matching_record:
                    subproduct = self.env["product.product"].search(
                        [
                            ("pnt_product_type", "=", "packing"),
                            (
                                "id",
                                "in",
                                record.product_id.pnt_parent_id.pnt_packing_ids.ids,
                            ),
                        ],
                        limit=1,
                    )
                    record.box_product_id = subproduct
                    invisible_fields = (
                        matching_record.id == record.product_id.id
                        or not record.parent_id.id
                    )

                else:
                    record.box_product_id = False
            record.invisible_fields = invisible_fields

    def action_open_stock_lot_boxes_wizard(self):
        return {
            "name": ("Add Boxes to Lot"),
            "type": "ir.actions.act_window",
            "res_model": "stock.lot.boxes.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_lot_id": self.id,
            },
        }


