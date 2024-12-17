{
    'name': 'Sale commission multiple',
    'version': '17.0.1.0.0',
    'category': '',
    'description': u"""
Several referrer per sale order or invoice (Enterprise Edition).
""",
    'author': 'Punt Sistemes SL',
    'depends': [
        'crm',
        'sale_management',
        'account',
        'partner_commission',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
}
