{
    'name': 'Sale commission multiple',
    'version': '17.0.1.0.0',
    'category': '',
    'description': u"""
Several referrer per sale order or invoice.
""",
    'author': 'Punt Sistemes SL',
    'depends': [
        'crm',
        'partner_commission',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
    ],
    'installable': True,
}
