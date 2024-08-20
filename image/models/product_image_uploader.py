import base64
import xlrd
import logging
import requests
from odoo import api, models

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model
    def process_excel_file(self):
        # Ruta del archivo Excel
        excel_path = '/opt/sources/odoo170/image.xlsx'

        # Abre el archivo Excel
        try:
            _logger.info("Abriendo el archivo Excel: %s", excel_path)
            wb = xlrd.open_workbook(excel_path)
            sheet = wb.sheet_by_index(0)
            _logger.info("El archivo tiene %d filas.", sheet.nrows)
        except Exception as e:
            _logger.error("Error al abrir el archivo Excel: %s", e)
            return

        # Itera sobre las filas del archivo Excel
        for row in range(1, sheet.nrows):  # Saltamos la primera fila (encabezados)
            name = sheet.cell_value(row, 0)
            image_url = sheet.cell_value(row, 1)
            product_ref = sheet.cell_value(row, 2)
            external_id = sheet.cell_value(row, 3)

            _logger.info(
                f"Procesando fila {row}: name={name}, image_url={image_url}, product_ref={product_ref}, external_id={external_id}")

            # Buscar el ID real de 'product_tmpl_id' usando la referencia externa
            product_template = self.env.ref(product_ref)
            if not product_template:
                _logger.warning(
                    f"No se encontró el producto con referencia {product_ref} en la fila {row}. Saltando...")
                continue

            # Convertir la imagen URL en base64
            try:
                _logger.info(f"Descargando imagen desde {image_url}...")
                image_data = base64.b64encode(requests.get(image_url).content)
                _logger.info(f"Imagen descargada y convertida a base64.")
            except Exception as e:
                _logger.error(f"Error al descargar la imagen para la fila {row}: {e}")
                continue

            # Crear el registro en el modelo 'product.image'
            try:
                _logger.info(f"Creando registro de imagen en Odoo para el producto con ID: {product_template.id}...")
                self.env['product.image'].create({
                    'name': name,
                    'image_1920': image_data,  # Campo de imagen
                    'product_tmpl_id': product_template.id,
                    'id': external_id
                })
                _logger.info(f"Imagen creada para el producto {name}.")
            except Exception as e:
                _logger.error(f"Error al crear la imagen en la fila {row}: {e}")
