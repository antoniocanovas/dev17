# Copyright 2023 Serincloud SL.
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Documents CRM",
    "summary": "Partner documents in CRM",
    "version": "17.0.1.0.0",
    'category': 'Sales',
    "author": "Punt Sistemes SL",
    "website": "https://www.puntsistemes.es",
    "license": "AGPL-3",
    "depends": [
        "contacts",
        "crm",
        "documents",
    ],
    "data": [
        "views/crm_lead_views.xml",
    ],
    "installable": True,
}
