# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


import logging

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    pnt_box_bag_id = fields.Many2one('product.template', string='Box Bag', domain="[('pnt_product_type','=','packaging')]")
    sscc_sequence_id = fields.Many2one(
        'ir.sequence',
        string='SSCC Sequence',
        help='Secuencia utilizada para generar el nombre de cualquier nuevo empaquetado '
             '(stock.quant.package). Si está definida, reemplaza la secuencia estándar de Odoo.',
    )
    pallet_packaging_ids = fields.Many2many(
        'stock.package.type',
        'res_company_pallet_package_type_rel',
        'company_id',
        'package_type_id',
        string='Pallet Packages',
        help='Tipos de paquete considerados palés. El botón Pallet2Pack en los albaranes '
             'asignará automáticamente un paquete destino a las líneas cuyo embalaje '
             'pertenezca a uno de estos tipos.',
    )
