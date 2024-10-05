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
    "name": 'Analytic distribution base',
    "version": '1.0',
    "depends": [
        'product',
        'account',
        'analytic',
    ],
    "author": "Punt Sistemes",
    "category": 'Account',
    "website": "https://www.puntsistemes.es",
    "description": """
        Base modelo for custom analytic distributions developed in customer modules. 
    """,
    "data": [
        'views/analytic_distribution_views.xml',
        'security/ir.model.access.csv',
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
}
