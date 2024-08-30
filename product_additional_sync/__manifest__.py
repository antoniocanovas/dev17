# Copyright 2021 IC - Pedro Guirao
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "eComerce Alternative Product Sync",
    "summary": "Al asignar un producto como alternativo o complementario, automáticamente se sincroniza bidireccionamente.",
    "version": "17.0.1.0.0",
    "category": "Website",
    "author": "Antonio Cánovas, ",
    "website": "",
    "license": "AGPL-3",
    "depends": [
        "website_sale",
        "base_automation",
                ],
    "data": [
        "data/action_server.xml",
    ],
    "installable": True,
}
