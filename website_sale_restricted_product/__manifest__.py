# Copyright 2023 Serincloud SL.
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Website sale restricted product",
    "summary": "New user type to restrict acces to website products to only allowed",
    "version": "17.0.1.0.0",
    "category": "Website",
    "author": "Serincloud SL",
    "website": "https://www.ingenieriacloud.com",
    "license": "AGPL-3",
    "depends": [
      'website_sale',
        'contacts',
    ],
    "data": [
        "security/user_groups.xml",
        "views/res_partner.xml",
        "data/server_actions.xml",
    ],
    "installable": True,
}
