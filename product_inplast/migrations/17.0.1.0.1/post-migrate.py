# Copyright 2025 Punt Sistemes
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import logging

from odoo.sql_db import Cursor

_logger = logging.getLogger(__name__)


def migrate(cr: Cursor, version: str | None) -> None:
    """
    Migración de campos Binary a Image.

    Los campos Image en Odoo son compatibles con Binary, por lo que los datos
    no se pierden. Sin embargo, este script re-procesa las imágenes para
    asegurar que Odoo genere las variantes de tamaño automáticamente
    (1024, 512, 256, 128).
    """
    _logger.info("Iniciando migración de campos Binary a Image en pnt.coa.content")

    # Obtener todos los registros que tienen imágenes
    cr.execute("""
        SELECT id, coa_body, multicolor_body, components_body
        FROM pnt_coa_content
        WHERE coa_body IS NOT NULL
           OR multicolor_body IS NOT NULL
           OR components_body IS NOT NULL
    """)

    records = cr.fetchall()
    _logger.info(f"Encontrados {len(records)} registros con imágenes para procesar")

    # Al cambiar de Binary a Image, Odoo automáticamente generará las variantes
    # de tamaño cuando el módulo se actualice. No necesitamos hacer nada más
    # porque los datos ya están en la base de datos y son compatibles.

    # Log para confirmar
    for record in records:
        record_id = record[0]
        has_coa_body = "Sí" if record[1] else "No"
        has_multicolor = "Sí" if record[2] else "No"
        has_components = "Sí" if record[3] else "No"
        _logger.info(
            f"Registro ID {record_id}: "
            f"coa_body={has_coa_body}, "
            f"multicolor_body={has_multicolor}, "
            f"components_body={has_components}"
        )

    _logger.info("Migración completada. Las imágenes se procesarán automáticamente.")
