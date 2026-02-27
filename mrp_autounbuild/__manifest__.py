# -*- coding: utf-8 -*-
{
    'name': 'MRP Auto Unbuild from Lot/Serial',
    'summary': """
        Allows to unbuild a serialized product in one step from the backend
        and from the Barcode App.
    """,
    'version': '17.0.1.0.0',
    'author': 'Odoo Community Association (OCA), Acanovas',
    'license': 'AGPL-3',
    'category': 'Manufacturing/Manufacturing',
    'website': 'https://github.com/OCA/mrp',
    'depends': [
        'mrp',
        'stock_barcode',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/stock_unbuild_wizard_views.xml',
        'views/product_template_views.xml',
        'views/stock_barcode_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mrp_autounbuild/static/src/components/main_menu.xml',
            'mrp_autounbuild/static/src/components/unbuild_barcode_handler.js',
            'mrp_autounbuild/static/src/components/unbuild_barcode_handler.xml',
        ],
    },
    'installable': True,
    'application': False,
}
