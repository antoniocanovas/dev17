{
    'name': 'Logistic Inplast',
    'version': '17.0.1.0.0',
    'category': '',
    'description': u"""
Logistic Inplast.
Gestión de envíos y compras en contenedores y camiones.
""",
    'author': 'Punt Sistemes SL',
    'depends': [
        'contacts',
        'product',
        'stock',
        'sale_stock',
        'sale_management',
        'custom_inplast',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/container_type_views.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/stock_picking_views.xml',
    ],
    'installable': True,
}
