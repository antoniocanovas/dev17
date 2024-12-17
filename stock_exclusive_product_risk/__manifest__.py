{
    'name': 'Stock exclusive product risk',
    'version': '17.0.1.0.0',
    'category': '',
    'description': u"""
Set the customer to products that are manufactured exclusively. 
Displays the stock value of exclusive products in the customer.""",
    'author': 'Punt Sistemes SL',
    'depends': [
        'product',
        'contacts',
        'account_financial_risk',
    ],
    'data': [
        'views/res_partner_views.xml',
        'views/product_template_views.xml',
    ],
    'installable': True,
}
