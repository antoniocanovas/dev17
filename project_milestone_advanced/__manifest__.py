# -*- coding: utf-8 -*-

{
    'name': 'Project Milestone advanced',
    'version': '17.0.1.0.0',
    'category': 'Project/Project',
    'summary': "Project Milestone menu and task count",
    'description': "New general menu."
                   "Task done by milestone",
    'author': 'Serincloud',
    'company': 'Serincloud',
    'maintainer': 'Serincloud',
    'website': 'https://www.ingenieriacloud.com',
    'depends': [
        'project_enterprise',
    ],

    'data': [
    'views/menu_views.xml',
    'views/project_milestone_view.xml',
    ],

    'assets': {},

    'images': ['static/description/icon.png'],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
