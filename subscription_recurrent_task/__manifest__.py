# © 2023 Serincloud ( https://www.ingenieriacloud.com )
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Subscription recurrent tasks',
    'version': '17.0.1.0.0',
    'category': '',
    "license": "AGPL-3",
    'website': "https://ingenieriacloud.com",
    'summary': 'Subscription recurrent tasks, to be used when each new invoice requires a new task.',
    'author': 'Serincloud',
    'depends': [
        'sale_management',
        'sale_subscription',
        'account',
        'project',
    ],
    'data': [
        'views/sale_subscription_plan_views.xml',
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
        'data/automatic_actions.xml',
    ],
    'installable': True,
    'application': False,
}
