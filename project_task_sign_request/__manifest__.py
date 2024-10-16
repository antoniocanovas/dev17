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
    "name": 'Project task Sign Requests',
    "version": '1.0',
    "depends": [
        'contacts',
        'project',
        'sign',
    ],
    "author": "Punt Sistemes",
    "category": 'Project',
    "website": "https://www.puntsistemes.es",
    "description": """
        This module links TASKS and SIGN REQUEST. 
    """,
    "data": [
        'views/sign_request_views.xml',
        'views/sign_send_request_views.xml',
        'views/project_task_views.xml',
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
}
