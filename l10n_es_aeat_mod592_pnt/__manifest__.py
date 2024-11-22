{
    'name': 'l10n_es_aeat_mod592 PNT',
    'version': '17.0.1.0.0',
    'category': '',
    'description': u"""
Impuesto al plástico.
""",
    'author': 'Punt Sistemes SL',
    'depends': [
        'mail',
        'contacts',
        'product',
        'stock',
        'sale_management',
        'account',
        'account_invoice_pricelist',
        'account_invoice_pricelist_sale',
        'product_pricelist_fixed_extra',
        'product_category_chatter',
    ],
    'data': [
        'views/account_move_views.xml',
        'views/account_move_line_views.xml',
        'views/product_category_views.xml',
        'views/product_pricelist_views.xml',
        'views/sale_order_views.xml',
        'views/res_company_views.xml',
        'views/product_template_views.xml',
    ],
    'installable': True,
}
