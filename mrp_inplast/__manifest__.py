{
    "name": "MRP Inplast",
    "summary": "MRP Inplast",
    "version": "17.0.1.0.0",
    'category': 'MRP',
    "author": "Punt Sistemes",
    "website": "https://www.puntsistemes.es",
    "Maintainers": [
        "Punt Sistemes",
    ],
    "license": "LGPL-3",
    "depends": [
        "product",
        "stock",
        "mrp_workorder",
        "maintenance",
        "mrp_maintenance",
        "custom_inplast",
        "product_inplast",
        "base_automation",
    ],
    "data": [
        "views/res_company_views.xml",
        "views/maintenance_equipment_views.xml",
        "views/product_template_views.xml",
        "views/mrp_bom_views.xml",
        "views/stocklot_view.xml",
        "data/server_actions.xml",
        "wizard/pallet_boxes_wizard_views.xml",
        "wizard/Confirm_Delete_Lot_Wizard_view.xml",
        "security/ir.model.access.csv",
    ],
    'assets': {
        'web.assets_backend': [
            'mrp_inplast/static/src/**/*.xml',
        ],
    },
    "installable": True,
}
