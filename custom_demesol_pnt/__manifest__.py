# Copyright 2023 Serincloud SL.
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Custom Demesol",
    "summary": "Customs Demesol",
    "version": "17.0.1.0.0",
    'category': 'Sales',
    "author": "Punt Sistemes SL",
    "website": "https://www.puntsistemes.es",
    "license": "AGPL-3",
    "depends": [
        "contacts",
        "hr_attendance",
    ],
    "data": [
        "views/res_partner_views.xml",
#        "data/automatic_actions.xml",
    ],
    "installable": True,
}
