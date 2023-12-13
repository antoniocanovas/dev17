# Copyright Serincloud SL - 2023
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "FV Watio Pico",
    "summary": "Watio Pico sale computation for energy sector.",
    "version": "17.0.1.0.0",
    "category": "sale",
    "author": "Serincloud SL",
    "website": "https://www.ingenieriacloud.com",
    "license": "AGPL-3",
    "depends": [
        "sale_management",
        "base_automation",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/wp_template_views.xml",
        "views/sale_order_views.xml",
        "views/product_views.xml",
        "views/menu_views.xml",
        "data/automatic_actions.xml",
    ],
    "installable": True,
}
