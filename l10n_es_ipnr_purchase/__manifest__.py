# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "INPR - Compras",
    "summary": "Impuesto especial sobre los envases de plástico no reutilizables ESPAÑA - Compras",
    "version": "17.0.1.0.1",
    "license": "AGPL-3",
    "author": "Pedro Guirao, Odoo Community Association (OCA)",
    "category": "Sales",
    "website": "https://github.com/OCA/l10n-spain",
    "depends": ["l10n_es_ipnr_account", "purchase"],
    "data": [
        "views/purchase_views.xml",
        "report/purchase_order_templates.xml",
        "report/purchase_quotation_templates.xml",
    ],
    "pre_init_hook": "pre_init_hook",
    "installable": True,
}
