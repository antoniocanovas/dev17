# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import datetime
from typing import Any

from odoo import api, fields, models
from odoo.exceptions import UserError


class MigInventario(models.Model):
    _name = "mig.inventario"
    _description = "MIG Inventario"

    name = fields.Char("Nombre Prod")
    ubicacion = fields.Char("ubicación")
    ubicacion_old = fields.Char("Ubicacion_old")
    lote = fields.Char("Lote")
    qty = fields.Float(string="qty")
    sscc1 = fields.Char("sscc1")
    sscc2 = fields.Char("sscc2")
    palet = fields.Char("Palet")
    boxsn = fields.Char("Box SN")

    lot_id = fields.Many2one("stock.lot", string="lot_id")
    product_id = fields.Many2one("product.product", string="Producto")
    location_id = fields.Many2one("stock.location", string="location")
    sml_id = fields.Many2one("stock.move.line", string="Stock move line")
    mig_fechafabricacion = fields.Date("Fecha fabricación")
    active = fields.Boolean(default=True, string="Activo")

    def _calcular_fecha_con_minutos_adicionales(
        self, fecha_fabricacion: object, nombre_lote: object
    ):
        """
        Calcula la fecha de fabricación sumando minutos adicionales según
        los últimos 3 dígitos del nombre del lote.
        """
        # Convertir fecha de texto a objeto datetime
        fecha_objeto = datetime.datetime.strptime(str(fecha_fabricacion), "%Y-%m-%d")

        # Extraer minutos a sumar de los últimos 3 dígitos del nombre del lote
        minutos_adicionales = 0
        if nombre_lote:
            try:
                # Extraer solo los dígitos del final del nombre
                digitos_finales = ""
                # Recorrer el nombre desde el final hacia atrás
                for char in reversed(nombre_lote):
                    if char.isdigit():
                        digitos_finales = char + digitos_finales
                    else:
                        break  # Parar cuando encuentre un carácter no numérico

                # Tomar máximo los últimos 3 dígitos
                if digitos_finales:
                    ultimos_3_digitos = (
                        digitos_finales[-3:]
                        if len(digitos_finales) >= 3
                        else digitos_finales
                    )
                    minutos_adicionales = int(ultimos_3_digitos)
            except ValueError:
                # Si hay error en la extracción, usar 0 minutos
                minutos_adicionales = 0

        # Sumar los minutos adicionales a la fecha
        if minutos_adicionales > 0:
            fecha_objeto += datetime.timedelta(minutes=minutos_adicionales)

        return fecha_objeto

    @api.model
    def _select_mig_fechafinfabricacion(self, record_date, parent_end_str):
        record_end_str = str(record_date) if record_date else False
        if not parent_end_str:
            return record_end_str

        parent_end_date = fields.Date.to_date(parent_end_str)
        if not parent_end_date:
            return record_end_str

        if not record_date or parent_end_date > record_date:
            return parent_end_str
        return record_end_str

    @api.model
    def _cron_update_mig_inventario(self):
        """Cron job that runs only if the new migration logic is NOT enabled."""
        if self.env.company.use_new_migration_logic:
            # Skip new version
            return

        recs = self.search([("sml_id", "=", False)])
        for r in recs:
            r._update_mig_inventario()

    @api.model
    def create(self, vals_list: Any) -> Any:
        """Sobrescribe create para ejecutar la actualización de inventario automáticamente."""
        records = super().create(vals_list)
        # Llamar a _update_mig_inventario o _update_new_mig_inventario según config
        if self.env.company.use_new_migration_logic:
            records._update_new_mig_inventario()
        else:
            records._update_mig_inventario()
        return records

    def _update_mig_inventario(self):
        # PROCEDIMIENTO:
        # 1. Los registros llegan a mig_inventario por creación manual o comunicación
        # RPC desde sistema antiguo.
        # 2. Este método regulariza inventario automáticamente para los registros
        #  con ubicación y producto detectados.
        # Quedan excluídos los que ya han sido regularizados (tienen sml_id asignado).
        for r in self:
            if r.name != "" and r.ubicacion and r.ubicacion_old and r.lote and r.palet:
                lote, ssccs = False, []

                # Busco la ubicación:
                locationname = (
                    r.ubicacion.strip() + " (" + r.ubicacion_old.strip() + ")"
                )
                location = self.env["stock.location"].search(
                    [("name", "=", locationname)]
                )
                if len(location.ids) > 1:
                    raise UserError(
                        "Varias ubicaciones con el mismo nombre: " + locationname
                    )

                # Busco el producto:
                productname = r.name.strip()
                product = self.env["product.product"].search(
                    [("default_code", "=", productname)]
                )
                if len(product.ids) > 1:
                    raise UserError(
                        "Varios productos con la misma referencia: " + productname
                    )

                # Crear lotes si no existen y actualizar inventario:
                if product.id and location.id and not r.sml_id.id:
                    nombrelote = r.lote + "/" + r.palet
                    lot = self.env["stock.lot"].search(
                        [("name", "=", nombrelote), ("product_id", "=", product.id)]
                    )
                    if lot.ids:
                        lote = lot[0].id
                        mig_date_str = (
                            str(r.mig_fechafabricacion)
                            if r.mig_fechafabricacion
                            else False
                        )
                        parentlotname = nombrelote.split("/")
                        parentlot = False

                        # Update Parent Logic
                        if parentlotname:
                            parentlot = self.env["stock.lot"].search(
                                [
                                    ("name", "=", parentlotname[0]),
                                    ("product_id", "=", product.id),
                                ]
                            )
                            if parentlot.id and r.mig_fechafabricacion:
                                current_end_str = parentlot.mig_fechafinfabricacion
                                update_parent = False
                                if not current_end_str:
                                    update_parent = True
                                else:
                                    current_end_date = fields.Date.to_date(
                                        current_end_str
                                    )
                                    if r.mig_fechafabricacion > current_end_date:
                                        update_parent = True
                                if update_parent:
                                    parentlot.write(
                                        {"mig_fechafinfabricacion": mig_date_str}
                                    )

                        # Update Child Lot Logic
                        if lot[0]:
                            desired_end_str = self._select_mig_fechafinfabricacion(
                                r.mig_fechafabricacion,
                                parentlot.mig_fechafinfabricacion
                                if parentlot
                                else False,
                            )
                            if (
                                desired_end_str
                                and desired_end_str != lot[0].mig_fechafinfabricacion
                            ):
                                lot[0].write(
                                    {"mig_fechafinfabricacion": desired_end_str}
                                )
                    else:
                        ssccs, parentlotname = [], False
                        parentlotname = nombrelote.split("/")
                        parentlot = self.env["stock.lot"].search(
                            [
                                ("name", "=", parentlotname[0]),
                                ("product_id", "=", product.id),
                            ]
                        )
                        mig_date_str = (
                            str(r.mig_fechafabricacion)
                            if r.mig_fechafabricacion
                            else False
                        )

                        if not parentlot.id and parentlotname:
                            parentlot = self.env["stock.lot"].create(
                                {
                                    "name": parentlotname[0],
                                    "mig_fechafabricacion": r.mig_fechafabricacion,
                                    "mig_fechafinfabricacion": mig_date_str,
                                    "product_id": product.id,
                                }
                            )
                        elif parentlot.id and r.mig_fechafabricacion:
                            current_end_str = parentlot.mig_fechafinfabricacion
                            update_parent = False
                            if not current_end_str:
                                update_parent = True
                            else:
                                current_end_date = fields.Date.to_date(
                                    current_end_str
                                )
                                if r.mig_fechafabricacion > current_end_date:
                                    update_parent = True
                            if update_parent:
                                parentlot.write(
                                    {"mig_fechafinfabricacion": mig_date_str}
                                )

                        if r.sscc1:
                            sscc1 = self.env["pnt.sscc.code"].create(
                                {"name": r.sscc1}
                            )
                            ssccs.append(sscc1.id)
                        if r.sscc2:
                            sscc2 = self.env["pnt.sscc.code"].create(
                                {"name": r.sscc2}
                            )
                            ssccs.append(sscc2.id)

                        desired_end_str = self._select_mig_fechafinfabricacion(
                            r.mig_fechafabricacion, parentlot.mig_fechafinfabricacion
                        )
                        lote = (
                            self.env["stock.lot"]
                            .create(
                                {
                                    "name": nombrelote,
                                    "mig_fechafabricacion": r.mig_fechafabricacion,
                                    "mig_fechafinfabricacion": desired_end_str,
                                    "product_id": product.id,
                                    "parent_id": parentlot.id,
                                    "sscc_code_ids": [(6, 0, ssccs)],
                                }
                            )
                            .id
                        )

                    # Procedimiento de inventariado automático:
                    newsm = self.env["stock.move"].create(
                        {
                            "name": product.name,
                            "product_id": product.id,
                            "location_id": 14,
                            "location_dest_id": location.id,
                            "product_uom_qty": r.qty,
                            "company_id": self.env.company.id,
                            "state": "done",
                        }
                    )
                    newsml = self.env["stock.move.line"].create(
                        {
                            "product_id": product.id,
                            "location_id": 14,
                            "location_dest_id": location.id,
                            "quantity": r.qty,
                            "company_id": self.env.company.id,
                            "lot_id": lote,
                            "move_id": newsm.id,
                            "state": "done",
                        }
                    )

                    # NUEVO: Actualizar fecha in_date del quant creado con minutos
                    # adicionales
                    if newsml.id:
                        quant = self.env["stock.quant"].search(
                            [
                                ("lot_id", "=", lote),
                                ("location_id", "=", location.id),
                                ("product_id", "=", product.id),
                            ],
                            limit=1,
                        )
                        if quant and r.mig_fechafabricacion:
                            # Usar el método auxiliar para calcular fecha con minutos
                            #  adicionales
                            fecha_final = self._calcular_fecha_con_minutos_adicionales(
                                r.mig_fechafabricacion, nombrelote
                            )
                            quant.write({"in_date": fecha_final})

                    # Registrar línea mig_inventario:
                    r.write(
                        {
                            "product_id": product.id,
                            "location_id": location.id,
                            "lot_id": lote,
                            "sml_id": newsml.id,
                        }
                    )

                    # Crear los lotes de las cajas:
                    if r.boxsn != "":
                        cajas = r.boxsn.split("/")
                        for caja in cajas:
                            caja = caja.split()
                            name = r.lote + "." + caja[0]
                            exist = self.env["stock.lot"].search(
                                [("name", "=", name), ("product_id", "=", product.id)]
                            )
                            if not exist:
                                parent_lot = self.env["stock.lot"].browse(lote)
                                desired_box_end_str = self._select_mig_fechafinfabricacion(
                                    r.mig_fechafabricacion,
                                    parent_lot.mig_fechafinfabricacion
                                    if parent_lot
                                    else False,
                                )
                                mrp_bom_template_id = r.product_id.mrp_bom_template_id.box_template_id.id
                                new_box = self.env["stock.lot"].create(
                                    {
                                        "name": name,
                                        "product_id": mrp_bom_template_id.id,
                                        "parent_id": lote,
                                        "mig_fechafabricacion": r.mig_fechafabricacion,
                                        "mig_fechafinfabricacion": desired_box_end_str,
                                    }
                                )
                                r.lot_id.related_boxes_ids = [(4, new_box.id)]

    def _validate_migration_config(self) -> Any:
        """Valida que la configuración de migración esté completa."""
        if not self.env.company.default_location_id:
            raise UserError(
                "Debe configurar la 'Ubicación migración' en la "
                "configuración de la compañía (Ajustes > Usuarios y "
                "Compañías > Compañías > pestaña Migración - modo debug)"
            )

        if not self.env.company.default_location_dest_id:
            raise UserError(
                "Debe configurar la 'Ubicación destino migración' en "
                "la configuración de la compañía (Ajustes > Usuarios "
                "y Compañías > Compañías > pestaña Migración - modo "
                "debug)"
            )

        picking_type = self.env["stock.picking.type"].search(
            [("code", "=", "internal"), ("company_id", "=", self.env.company.id)],
            limit=1,
        )

        if not picking_type:
            raise UserError(
                "No se encontró un tipo de operación de traslado "
                "interno para esta compañía"
            )

        return picking_type

    def _get_product_packaging_info(self, product: Any) -> tuple[Any, Any, Any]:
        """Obtiene el empaquetado del producto y su tipo de paquete."""
        product_packaging = self.env["product.packaging"].search(
            [("product_id", "=", product.id)], limit=1
        )

        packaging_id = product_packaging.id if product_packaging else False
        package_type_id = (
            product_packaging.package_type_id.id
            if product_packaging and product_packaging.package_type_id
            else False
        )

        return product_packaging, packaging_id, package_type_id

    def _create_package(self, sscc_name: str, package_type_id: Any) -> Any:
        """Crea un paquete con el nombre del SSCC y el tipo de paquete."""
        if not sscc_name:
            return False

        package_vals = {"name": sscc_name}
        if package_type_id:
            package_vals["package_type_id"] = package_type_id

        package = self.env["stock.quant.package"].create(package_vals)
        return package.id

    def _get_or_create_lot(
        self,
        product: Any,
        lot_name: str,
        parent_lot_name: str,
        fabrication_date: Any,
    ) -> tuple[int, str, str]:
        """Obtiene o crea un lote con su lote padre y códigos SSCC.

        Returns:
            tuple[lot_id, sscc1_name, sscc2_name]: El ID del lote y los nombres de
             SSCC1 y SSCC2 generados
        """
        mig_date_str = str(fabrication_date) if fabrication_date else False

        # 1. Gestionar Lote Padre (Buscar o Crear y Actualizar Fechas)
        parent_lot = self.env["stock.lot"].search(
            [
                ("name", "=", parent_lot_name),
                ("product_id", "=", product.id),
            ]
        )

        if not parent_lot:
            parent_lot = self.env["stock.lot"].create(
                {
                    "name": parent_lot_name,
                    "mig_fechafabricacion": fabrication_date,
                    "mig_fechafinfabricacion": mig_date_str,
                    "product_id": product.id,
                }
            )
        elif fabrication_date:
            # Actualizar fecha fin fabricación del padre si es necesario
            current_end_str = parent_lot.mig_fechafinfabricacion
            update_parent = False
            if not current_end_str:
                update_parent = True
            else:
                current_end_date = fields.Date.to_date(current_end_str)
                if fabrication_date > current_end_date:
                    update_parent = True

            if update_parent:
                parent_lot.write({"mig_fechafinfabricacion": mig_date_str})

        # 2. Gestionar Lote Hijo (Buscar o Crear)
        lot = self.env["stock.lot"].search(
            [("name", "=", lot_name), ("product_id", "=", product.id)]
        )

        # Calcular fecha fin deseada para el lote hijo
        desired_end_str = self._select_mig_fechafinfabricacion(
            fabrication_date, parent_lot.mig_fechafinfabricacion
        )

        if lot:
            # Si el lote ya existe, actualizar fecha fin y obtener sus SSCCs
            if desired_end_str and desired_end_str != lot[0].mig_fechafinfabricacion:
                lot[0].write({"mig_fechafinfabricacion": desired_end_str})

            sscc_codes = lot[0].sscc_code_ids
            sscc1_name = sscc_codes[0].name if len(sscc_codes) > 0 else ""
            sscc2_name = sscc_codes[1].name if len(sscc_codes) > 1 else ""
            return lot[0].id, sscc1_name, sscc2_name

        # Crear lote (sin SSCC previos, se generarán automáticamente)
        new_lot = self.env["stock.lot"].create(
            {
                "name": lot_name,
                "mig_fechafabricacion": fabrication_date,
                "mig_fechafinfabricacion": desired_end_str,
                "product_id": product.id,
                "parent_id": parent_lot.id,
            }
        )

        # Generar SSCC automáticamente usando la función del lote
        # Si el producto tiene pnt_product_two_sscc, generar 2 SSCC en lugar de 1
        qty_sscc = 2 if product.pnt_product_two_sscc else 1
        new_lot.get_next_sscc(qty=qty_sscc)

        # Obtener los SSCC recién generados
        sscc_codes = new_lot.sscc_code_ids
        # Los últimos códigos generados están al final
        if qty_sscc == 2:
            sscc1_name = sscc_codes[-2].name if len(sscc_codes) >= 2 else ""
            sscc2_name = sscc_codes[-1].name if len(sscc_codes) >= 1 else ""
        else:
            sscc1_name = sscc_codes[-1].name if len(sscc_codes) >= 1 else ""
            sscc2_name = ""

        return new_lot.id, sscc1_name, sscc2_name

    def _create_inventory_adjustment(
        self,
        product: Any,
        lot_id: int,
        location: Any,
        qty: float,
        package_id: Any,
        packaging_id: Any,
    ) -> tuple[Any, Any]:
        """Crea un ajuste de inventario (movimiento de stock) para el producto.

        Returns:
            tuple[move_line, quant_id]: La línea de movimiento creada y el ID del
            quant generado
        """
        # Crear movimiento de stock
        stock_move = self.env["stock.move"].create(
            {
                "name": product.name,
                "product_id": product.id,
                "location_id": 14,  # Virtual Inventory location
                "location_dest_id": location.id,
                "product_uom_qty": qty,
                "company_id": self.env.company.id,
                "state": "done",
            }
        )

        # Crear línea de movimiento
        move_line = self.env["stock.move.line"].create(
            {
                "product_id": product.id,
                "location_id": 14,
                "location_dest_id": location.id,
                "quantity": qty,
                "company_id": self.env.company.id,
                "lot_id": lot_id,
                "move_id": stock_move.id,
                "state": "done",
            }
        )

        # Asignar paquete y packaging después de crear la línea
        vals_to_write = {}
        if package_id:
            vals_to_write["result_package_id"] = package_id
        if packaging_id:
            vals_to_write["product_packaging_id"] = packaging_id

        if vals_to_write:
            move_line.write(vals_to_write)

        # Obtener el quant creado por este ajuste de inventario
        # IMPORTANTE: Filtrar también por package_id para obtener el quant correcto
        search_domain = [
            ("lot_id", "=", lot_id),
            ("location_id", "=", location.id),
            ("product_id", "=", product.id),
        ]

        # Agregar filtro de paquete si existe
        if package_id:
            search_domain.append(("package_id", "=", package_id))

        quant = self.env["stock.quant"].search(search_domain, limit=1)

        return move_line, quant.id if quant else False

    def _update_quant_date(
        self,
        product: Any,
        lot_id: int,
        location: Any,
        lot_name: str,
        fabrication_date: Any,
    ) -> None:
        """Actualiza la fecha in_date del quant con minutos adicionales."""
        quant = self.env["stock.quant"].search(
            [
                ("lot_id", "=", lot_id),
                ("location_id", "=", location.id),
                ("product_id", "=", product.id),
            ],
            limit=1,
        )

        if quant and fabrication_date:
            fecha_final = self._calcular_fecha_con_minutos_adicionales(
                fabrication_date, lot_name
            )
            quant.write({"in_date": fecha_final})

    def _get_or_create_internal_picking(
        self, picking_type: Any, location_src: Any, location_dest: Any
    ) -> Any:
        """Busca o crea un picking de traslado interno."""
        # Buscar pickings existentes que no estén validados ni cancelados
        existing_picking = self.env["stock.picking"].search(
            [
                ("picking_type_id", "=", picking_type.id),
                ("location_id", "=", location_src.id),
                ("location_dest_id", "=", location_dest.id),
                ("state", "in", ["draft", "waiting", "confirmed", "assigned"]),
            ],
            limit=1,
        )

        if existing_picking:
            return existing_picking

        return self.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "location_id": location_src.id,
                "location_dest_id": location_dest.id,
                "company_id": self.env.company.id,
            }
        )

    def _create_internal_transfer_move(
        self,
        picking: Any,
        product: Any,
        lot_id: int,
        qty: float,
        location_src: Any,
        location_dest: Any,
        package_id: Any,
        product_packaging: Any,
        packaging_id: Any,
        quant_id: Any = False,
    ) -> Any:
        """
        Crea un movimiento de traslado interno con aplicación de
        reglas de putaway.

        Args:
            quant_id: ID del quant que debe ser recolectado por este movimiento
        """
        # Buscar si existe un movimiento idéntico en el picking
        existing_move = self.env["stock.move"].search(
            [
                ("picking_id", "=", picking.id),
                ("product_id", "=", product.id),
                ("location_id", "=", location_src.id),
                ("location_dest_id", "=", location_dest.id),
                ("product_packaging_id", "=", packaging_id),
                ("state", "!=", "cancel"),
            ],
            limit=1,
        )

        if existing_move:
            # Actualizar la cantidad del movimiento existente
            new_qty = existing_move.product_uom_qty + qty
            existing_move.write({"product_uom_qty": new_qty})
            transfer_move = existing_move
        else:
            # Crear movimiento de stock en el estado correcto
            move_vals = {
                "name": product.name,
                "product_id": product.id,
                "product_uom_qty": qty,
                "product_uom": product.uom_id.id,
                "picking_id": picking.id,
                "location_id": location_src.id,
                "location_dest_id": location_dest.id,
                "company_id": self.env.company.id,
                "product_packaging_id": packaging_id,
            }

            # Si el picking ya está asignado, crear el movimiento en estado asignado
            if picking.state in ["assigned", "confirmed"]:
                move_vals["state"] = "assigned"

            transfer_move = self.env["stock.move"].create(move_vals)

        # Solo confirmar si el picking está en draft
        if picking.state == "draft":
            picking.action_confirm()
            transfer_move._action_assign()
        elif picking.state in ["assigned", "confirmed"]:
            # Si el picking ya está asignado, crear la línea manualmente
            move_line_vals = {
                "move_id": transfer_move.id,
                "product_id": product.id,
                "lot_id": lot_id,
                "quantity": qty,
                "product_uom_id": product.uom_id.id,
                "location_id": location_src.id,
                "location_dest_id": location_dest.id,
                "picking_id": picking.id,
                "company_id": self.env.company.id,
            }
            # Asignar el quant_id si está disponible
            if quant_id:
                move_line_vals["quant_id"] = quant_id

            transfer_line = self.env["stock.move.line"].create(move_line_vals)
        else:
            # Para otros estados, usar _action_assign
            transfer_move._action_assign()

        # Obtener la línea creada
        if "transfer_line" not in locals():
            transfer_line = (
                transfer_move.move_line_ids[0] if transfer_move.move_line_ids else False
            )

        if not transfer_line:
            return False

        # Asignar paquete, packaging y quant_id
        vals_to_write = {}
        if package_id:
            vals_to_write["result_package_id"] = package_id
        if packaging_id:
            vals_to_write["product_packaging_id"] = packaging_id
        # Asignar quant_id si no se asignó en la creación (casos draft/otros estados)
        if quant_id and not transfer_line.quant_id:
            vals_to_write["quant_id"] = quant_id

        if vals_to_write:
            transfer_line.write(vals_to_write)

        # Aplicar reglas de putaway
        self._apply_putaway_rules(
            transfer_line, product, qty, location_dest, package_id, product_packaging
        )

        return transfer_line

    def _apply_putaway_rules(
        self,
        move_line: Any,
        product: Any,
        qty: float,
        location_dest: Any,
        package_id: Any,
        product_packaging: Any,
    ) -> None:
        """Aplica las reglas de putaway para determinar la ubicación."""
        self.env.flush_all()

        package_obj = (
            self.env["stock.quant.package"].browse(package_id) if package_id else None
        )
        packaging_obj = product_packaging if product_packaging else None

        putaway_location = location_dest._get_putaway_strategy(
            product, quantity=qty, package=package_obj, packaging=packaging_obj
        )

        if putaway_location:
            move_line.write({"location_dest_id": putaway_location.id})

    def _create_box_lots(
        self,
        product: Any,
        parent_lot_id: int,
        box_sn: str,
        lot_base_name: str,
        fabrication_date: Any,
    ) -> None:
        """Crea lotes para las cajas individuales basados en el box SN."""
        if not box_sn:
            return

        parent_lot = self.env["stock.lot"].browse(parent_lot_id)
        cajas = box_sn.split("/")

        for caja in cajas:
            caja_parts = caja.split()
            if not caja_parts:
                continue

            box_name = f"{lot_base_name}.{caja_parts[0]}"

            # Verificar si ya existe
            existing_box = self.env["stock.lot"].search(
                [("name", "=", box_name), ("product_id", "=", product.id)]
            )

            if not existing_box:
                desired_box_end_str = self._select_mig_fechafinfabricacion(
                    fabrication_date,
                    parent_lot.mig_fechafinfabricacion if parent_lot else False,
                )

                new_box = self.env["stock.lot"].create(
                    {
                        "name": box_name,
                        "product_id": product.id,
                        "parent_id": parent_lot_id,
                        "mig_fechafabricacion": fabrication_date,
                        "mig_fechafinfabricacion": desired_box_end_str,
                    }
                )
                parent_lot.related_boxes_ids = [(4, new_box.id)]

    def _update_new_mig_inventario(self) -> None:
        """
        Procesa registros de migración de inventario.  Procedimiento:
        1. Los registros llegan a mig_inventario por creación manual o
           RPC desde sistema antiguo
        2. Este método regulariza inventario automáticamente para
           registros con producto y ubicación
        3. Quedan excluidos los que ya han sido regularizados
           (tienen sml_id asignado)
        """
        # Validar configuración de migración
        picking_type = self._validate_migration_config()

        location = self.env.company.default_location_id
        location_dest = self.env.company.default_location_dest_id

        for record in self:
            # Validar que el registro tenga los datos necesarios
            if (
                not all(
                    [
                        record.name,
                        record.lote,
                        record.palet,
                    ]
                )
                or record.qty <= 0
            ):
                continue

            # Buscar producto
            product = self.env["product.product"].search(
                [("default_code", "=", record.name.strip())]
            )
            if len(product) > 1:
                ref = record.name.strip()
                raise UserError(f"Varios productos con la misma referencia: {ref}")

            if not product or not location or record.sml_id:
                continue

            # Preparar nombres de lotes
            lot_name = f"{record.lote}/{record.palet}"
            parent_lot_name = record.lote

            ######################################################################
            # 1. Obtener o crear lote con SSCC
            # - Si pnt_product_two_sscc = True: genera 2 SSCC automáticos
            # - Si pnt_product_two_sscc = False: genera 1 SSCC automático
            lot_id, sscc1_generated, sscc2_generated = self._get_or_create_lot(
                product,
                lot_name,
                parent_lot_name,
                record.mig_fechafabricacion,
            )
            ######################################################################
            # 2. Obtener información de empaquetado
            product_packaging, packaging_id, package_type_id = (
                self._get_product_packaging_info(product)
            )
            ######################################################################
            # 3. Crear paquete con el SSCC1 generado automáticamente
            package_id = self._create_package(sscc1_generated, package_type_id)

            # 4. Crear ajuste de inventario inicial
            move_line, quant_id = self._create_inventory_adjustment(
                product, lot_id, location, record.qty, package_id, packaging_id
            )
            ######################################################################
            # 5. Actualizar fecha del quant
            self._update_quant_date(
                product, lot_id, location, lot_name, record.mig_fechafabricacion
            )
            ######################################################################
            # 6. Registrar datos en mig_inventario
            record.write(
                {
                    "product_id": product.id,
                    "location_id": location.id,
                    "lot_id": lot_id,
                    "sml_id": move_line.id,
                    "sscc1": sscc1_generated,
                    "sscc2": sscc2_generated,
                }
            )
            ######################################################################
            # 7. Crear o reutilizar picking de traslado interno
            picking = self._get_or_create_internal_picking(
                picking_type, location, location_dest
            )
            ######################################################################
            # 8. Crear movimiento de traslado con putaway
            # El quant_id asegura que se recoja exactamente el quant del ajuste
            self._create_internal_transfer_move(
                picking,
                product,
                lot_id,
                record.qty,
                location,
                location_dest,
                package_id,
                product_packaging,
                packaging_id,
                quant_id,
            )
            ######################################################################
            # 9. Crear lotes de cajas
            self._create_box_lots(
                product, lot_id, record.boxsn, record.lote, record.mig_fechafabricacion
            )
            #######################################################################
