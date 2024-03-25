# © 2023 Punt Sistemes ( https://www.puntsistemes.es )
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Power CUPS',
    'version': '17.0.1.0.0',
    'category': '',
    "license": "AGPL-3",
    'website': "https://www.puntsistemes.es",
    'summary': 'Power CUPS',
    'author': 'Punt Sistemes',
    'depends': [
        'mail',
        'contacts',
        'crm',
        'project',
        'sale_management',
    ],
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'views/power_cups_views.xml',
        'views/power_cups_shared_views.xml',
        'views/res_partner_views.xml',
        'views/crm_lead_views.xml',
        'views/project_project_views.xml',
        'views/project_task_views.xml',
        'views/sale_order_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
}
