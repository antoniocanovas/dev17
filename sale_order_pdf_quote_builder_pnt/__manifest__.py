# -*- coding: utf-8 -*-

{
    'name': 'Sale Order Quote PDF Builder',
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'summary': "PDF Template from Sale Order",
    'description': "Add option to include sale_template from sale.order, by default only on sale.order.template",
    'author': 'Antonio Cánovas',
    'company': 'Punt Sistemes',
    'maintainer': 'Punt Sistemes',
    'website': 'https://www.ingenieriacloud.com',
    'depends': [
        'sale_management',
        #'sale_pdf_quote_builder',
    ],
    'data': [
        'views/sale_order_views.xml',
    ],
    'assets': {},

    'images': ['static/description/icon.png'],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
