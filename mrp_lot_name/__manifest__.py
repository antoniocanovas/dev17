{
    "name": "MRP Lot name strategy",
    "summary": "Force lot name in MRP Manufacturing Orders",
    "version": "17.0.1.0.0",
    'category': 'MRP',
    'description': u"""
    Set name mode on Company configuration and it will be applied on manufacturing confirmation.
    """,
    "author": "Punt Sistemes",
    "website": "https://www.puntsistemes.es",
    "Maintainers":[
        "Punt Sistemes",
    ],
    "license": "LGPL-3",
    "depends": [
        "product",
        "stock",
        "mrp",
    ],
    "data": [
        "views/res_company_views.xml"
    ],
    "installable": True,
}
