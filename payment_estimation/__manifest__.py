# -*- coding: utf-8 -*-
##############################################################################
#
#    Punt Sistemes SL
#    Copyright (C) 2024 - Punt Sistemes (http://www.puntsistemes.es). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

{
    "name": 'Payment estimations',
    "version": '1.0',
    "depends": [
        'account',
    ],
    "author": "Punt Sistemes",
    "category": 'Account Reports',
    "website": "https://www.puntsistemes.es",
    "description": """
        New future estimation payments, and report with unpaid invoices. 
    """,
    "data": [
        'security/ir.model.access.csv',
        'views/menu_views.xml',
        'views/res_partner_views.xml',
        'views/product_attribute_value_views.xml',
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
}
