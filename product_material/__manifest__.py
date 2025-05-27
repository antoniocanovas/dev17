# Copyright Punt Sistemes SL - 2025
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Product material",
    "summary": "Product materials in products",
    "version": "17.0.1.0.0",
    "category": "stock",
    "author": "Punt Sistemes SL",
    "website": "https://www.puntsistemes.es",
    "license": "AGPL-3",
    "depends": [
        # ODOO:
        "stock",
        # OCA:
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/product_material_views.xml",
        "views/product_template_views.xml",
    ],
    "installable": True,
}
