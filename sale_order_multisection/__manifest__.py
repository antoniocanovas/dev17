{
    'name': 'Sale Order Multisection',
    'version': '17.0.1.0.0',
    'category': '',
    'description': u"""

""",
    'author': 'Serincloud',
    'depends': [
        'sale_management',
        'base_automation',

    ],
    'data': [
        'views/sale_order_views.xml',
        'security/ir.model.access.csv',
        'data/automatic_actions.xml',
        'views/report_sale_order.xml',
        'views/account_report.xml',
    ],
    'installable': True,
}
