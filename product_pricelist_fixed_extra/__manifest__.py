{
    'name': 'Product pricelist fixed extra',
    'version': '17.0.1.0.0',
    'category': '',
    'description': u"""
Product pricelist price extra option as selection
""",
    'author': 'Punt Sistemes SL',
    'depends': [
        'product',
        'sale_management',
    ],
    'data': [
        'views/product_pricelist_item_views.xml',
        'views/product_pricelist_views.xml',
    ],
     'installable': True,
    'application': True,
}