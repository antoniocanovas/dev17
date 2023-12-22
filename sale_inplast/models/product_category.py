from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class ProductCategory(models.Model):
    _inherit = 'product.category'

    pnt_raw_material = fields.Many2one('product.template', store=True, copy=True, string='Raw material',
                                       domain="[('detailed_type','=','product')]",
                                       help='Main component to manufacture these category products.')
    pnt_plastic_weight = fields.Float('Plastic weight', store=True, copy=True, digits='Stock Weight',
                                      help='Unit weight used to pricelist recalculation and plastic taxes.')
    pnt_mrp_fault_percent = fields.Float('Fault (%)', store=True, copy=True,
                                         help='Production percent deficiency')

    # Incremento tanto por mil debido a variaciones del coste de materia prima y energía:
    pnt_i0 = fields.Float('Inc. Raw (tanto/1000)', store=True, copy=False)
    # Primer incremento comercial porcentual sobre el precio ya modificado por variación de precio en MP + defectuoso:
    pnt_i1 = fields.Float('Inc. 1 (%)', store=True, copy=False)
    # Segundo incremento en tanto por mil, sobre el precio ya modificado por variación de precio en MP + defectuoso:
    pnt_i2 = fields.Float('Inc. 2 (tanto/1000)', store=True, copy=False)
    # Tercer incremento en valor absoluto sobre los incrementos anteriores:
    pnt_i3 = fields.Float('Inc. 3 (€)', store=True, copy=False)

    pnt_is_manufactured = fields.Boolean('Manufactured', store=True, copy=True, default=True,
                                         help='Enabled if products are manufactured, disabled when bought.')