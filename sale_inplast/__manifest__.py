{
    'name': 'Custom Inplast Sales',
    'version': '17.0.1.0.0',
    'category': '',
    'description': u"""
Custom Inplast Sales.
Cada cliente sólo tiene posibilidad de ser ofertado en sus productos (ventas, facturas, tarifas, etc).
Recálculo de tarifas en base a datos de familia, productos y materia prima.
""",
    'author': 'Punt Sistemes SL',
    'depends': [
        'mail',
        'contacts',
        'product',
        'sale_management',
        'account',
        'account_invoice_pricelist',
        'account_invoice_pricelist_sale',
        'product_pricelist_fixed_extra',
    ],
    'data': [
        'views/account_move_views.xml',
        'views/product_category_views.xml',
        'views/product_pricelist_views.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/res_company_views.xml',
        'views/product_template_views.xml',
    ],
    'installable': True,
}
