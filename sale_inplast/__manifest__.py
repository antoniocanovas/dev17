{
    'name': 'Sales Inplast',
    'version': '17.0.1.0.0',
    'category': '',
    'description': u"""
Sales Inplast.
Cada cliente sólo tiene posibilidad de ser ofertado en sus productos (ventas, facturas, tarifas, etc).
Recálculo de tarifas en base a datos de familia, productos y materia prima.
""",
    'author': 'Punt Sistemes SL',
    'depends': [
        'mail',
        'contacts',
        'product',
        'stock',
        'sale_management',
        'account',
        'l10n_es',
        'account_invoice_pricelist',
        'account_invoice_pricelist_sale',
        'product_category_chatter',
        'l10n_es_ipnr_account',
        'product_inplast',
        'mrp_inplast',
    ],
    'data': [
        'views/account_move_views.xml',
        'views/ir_actions_report_templates.xml',
        'views/product_category_views.xml',
        'views/product_pricelist_views.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/res_company_views.xml',
        'views/product_product_views.xml',
        'data/server_actions.xml',
    ],
    'installable': True,
}
