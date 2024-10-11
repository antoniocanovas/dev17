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
    "name": 'Project task expirations',
    "version": '1.0',
    "depends": [
        'contact',
        'project',
    ],
    "author": "Punt Sistemes",
    "category": 'Project',
    "website": "https://www.puntsistemes.es",
    "description": """
        It allows control through tasks or activities, the monitoring of certifications 
        or documents that must be accepted or completed by collaborators. 
        For example, suppliers who must send food quality certificates, employee certifications, 
        employment contracts, social security documents, etc. 
        This information will appear in each collaborator's card. 
        Operationally, the project must be marked as "Is expiration". 
    """,
    "data": [
        'views/project_project_views.xml',
        'views/res_partner_views.xml',
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
}
