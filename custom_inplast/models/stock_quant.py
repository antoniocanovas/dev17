# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import datetime

from odoo import api, fields, models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    # Campo computed para mostrar la fecha de fabricación del lote
    lot_fabrication_date = fields.Char(
        string="Fecha Fabricación Lote",
        compute="_compute_lot_fabrication_date",
        store=False,
    )

    @api.depends("lot_id", "lot_id.mig_fechafabricacion")
    def _compute_lot_fabrication_date(self):
        """
        Computa la fecha de fabricación del lote asociado al quant.
        """
        for quant in self:
            if quant.lot_id and quant.lot_id.mig_fechafabricacion:
                quant.lot_fabrication_date = quant.lot_id.mig_fechafabricacion
            else:
                quant.lot_fabrication_date = ""

    def update_quant_in_date_from_fabrication(self):
        """
        Actualiza el campo 'in_date' de los quants basándose en la fecha
        de fabricación del lote asociado, sumando minutos según los últimos
        3 dígitos del nombre del lote.
        """
        for quant in self:
            if quant.lot_id and quant.lot_id.mig_fechafabricacion:
                fecha_texto = quant.lot_id.mig_fechafabricacion
                # Convertir fecha de texto a objeto datetime
                fecha_objeto = datetime.datetime.strptime(fecha_texto, "%Y-%m-%d")

                # Extraer minutos a sumar de los últimos 3 dígitos del nombre del lote
                minutos_adicionales = 0
                if quant.lot_id.name:
                    nombre_lote = quant.lot_id.name
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

                # Actualizar el campo 'in_date' del quant
                quant.write({"in_date": fecha_objeto})

    def action_assign_packages_from_sscc(self):
        """
        Asigna paquetes a los quants seleccionados basándose en los SSCCs
        almacenados en sus lotes.

        Este método es útil para corregir inventario ya existente que no
        tiene paquetes asignados, permitiendo que las reglas de putaway
        funcionen correctamente.
        """
        for quant in self:
            # Solo procesar quants con lote, sin paquete y con cantidad
            if not quant.lot_id or quant.package_id or quant.quantity <= 0:
                continue

            # Obtener el lote
            lot = quant.lot_id
            if not lot.sscc_code_ids:
                continue

            # Obtener el primer SSCC del lote
            sscc_name = lot.sscc_code_ids[0].name if lot.sscc_code_ids else False
            if not sscc_name:
                continue

            # Obtener información de empaquetado del producto
            product_packaging = self.env["product.packaging"].search(
                [("product_id", "=", quant.product_id.id)], limit=1
            )

            package_type_id = (
                product_packaging.package_type_id.id
                if product_packaging and product_packaging.package_type_id
                else False
            )

            # Buscar o crear el paquete con el SSCC
            package = self.env["stock.quant.package"].search(
                [("name", "=", sscc_name)], limit=1
            )

            if not package:
                package_vals = {"name": sscc_name}
                if package_type_id:
                    package_vals["package_type_id"] = package_type_id
                package = self.env["stock.quant.package"].create(package_vals)

            # Asignar el paquete al quant
            quant.write({"package_id": package.id})

