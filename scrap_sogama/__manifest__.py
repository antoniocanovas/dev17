# -*- coding: utf-8 -*-
{
    'name': "Scrap Sogama",

    'summary': """
        Añade campos de peso para la gestión de residuos en los albaranes.""",

    'description': """
        Este módulo añade nuevos campos de peso (férreo, no férreo, metales, plástico) al modelo stock.picking.
        - Nueva pestaña "Sogama" en la vista de formulario de albaranes.
        - Campos editables en la vista de lista.
    """,

    'author': "Your Company",
    'website': "https://www.yourcompany.com",

    'category': 'Inventory',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['stock'],

    # always loaded
    'data': [
        'views/stock_picking_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
