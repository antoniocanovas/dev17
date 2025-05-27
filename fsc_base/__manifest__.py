# © 2023 Serincloud ( https://www.puntsistemes.es )
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'FSC',
    'version': '18.0.1.0.0',
    'category': 'mrp',
    "license": "AGPL-3",
    'website': "https://puntsistemes.es",
    'summary': 'FSC Traceability',
    'author': 'Punt Sistemes',
    'depends': [
        'sale_management',
        'purchase',
        'stock',
        'mrp',
        'product_material',
        'base_automation',
        'mail',
        'account_intrastat',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_material_views.xml',
        'views/mrp_production_views.xml',
        'views/stock_lot_views.xml',
        'views/product_views.xml',
        'views/fsc_audit_views.xml',
        'views/fsc_audit_product_views.xml',
        'views/eutr_audit_views.xml',
        'views/res_company_views.xml',
        'data/automatic_actions.xml',
    ],
    'installable': True,
    'application': False,
}
