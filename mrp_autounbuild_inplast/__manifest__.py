# -*- coding: utf-8 -*-
{
    'name': 'MRP Auto Unbuild Inplast',
    'summary': 'Extiende mrp_autounbuild: al descomponer un palet (packing/pallet) '
               'descompone automáticamente las cajas relacionadas usando los números '
               'de serie de related_boxes_ids.',
    'version': '17.0.1.0.0',
    'author': 'Acanovas',
    'license': 'AGPL-3',
    'category': 'Manufacturing',
    'depends': [
        'mrp_autounbuild',
        'mrp_inplast',
    ],
    'data': [
        'views/res_company_views.xml',
    ],
    'installable': True,
    'application': False,
}
