# © 2023 Serincloud ( https://www.puntsistemes.es )
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'FSC',
    'version': '17.0.1.0.0',
    'category': 'mrp',
    "license": "AGPL-3",
    'website': "https://puntsistemes.es",
    'summary': 'FSC Attributes',
    'author': 'Punt Sistemes',
    'depends': [
        'stock',
        'mrp',
        'fsc_base',
    ],
    'data': [
        'views/res_company_views.xml',
        'views/product_views.xml',
    ],
    'installable': True,
    'application': False,
}
