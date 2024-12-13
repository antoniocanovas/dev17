# © 2023 Serincloud ( https://www.ingenieriacloud.com )
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Account financial risk contracts',
    'version': '17.0.3.0.0',
    'category': '',
    "license": "AGPL-3",
    'website': "https://www.ingenieriacloud.com",
    'summary': 'Risk contracts history and details',
    'author': 'Serincloud',
    'depends': [
        'account',
        'account_financial_risk',
        'base_automation',
        'account_payment_mode',
        'account_payment_partner',
    ],
    'data': [
        'views/res_partner_views.xml',
        'views/risk_contract_views.xml',
        'views/risk_batch_views.xml',
        'views/account_move_views.xml',
        'views/menu_views.xml',
        'views/account_payment_mode_views.xml',
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'data/server_actions.xml',
    ],
    'installable': True,
    'application': False,
}
