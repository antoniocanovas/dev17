{
    'name': 'Sale Order Multisection Discount',
    'version': '16.0.1.0.0',
    'category': '',
    'license': 'AGPL-3',
    'description': u"""
Wizard discounts for multisections sales orders
""",
    'author': 'Serincloud',
    'depends': [
        'sale_order_multisection',
    ],
    'data': [
        'data/server_actions.xml',
        'views/sale_order_wizard_multisection_discount.xml',
        'views/sale_order_views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
}
