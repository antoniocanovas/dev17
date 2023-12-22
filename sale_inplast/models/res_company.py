# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


import logging

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    pnt_pricelist_day_lock = fields.Integer('Pricelist days lock', store=True, default=15)
    pnt_update_month_day = fields.Integer('Pricelist update day', store=True, default=1)
    pnt_product_plastic_tax_id = fields.Many2one('product.template', string='Plastic tax product', store=True,
                                                 help='Selecciona un producto, ya te hemos preparado uno (busca por AEAT).'
                                                      'Si cambian los importes del impuesto, cámbialo en este producto.')
    pnt_plastic_sale_tax = fields.Float('Sale tax (€/kg)', store=False,
                                        related='pnt_product_plastic_tax_id.list_price',
                                        help='Tasa de impuesto por kg de plástico fabricado en España. '
                                             'Es recuperable si es vendido fuera de España')
    pnt_plastic_purchase_tax = fields.Float('Purchase tax (€/kg)', store=False,
                                            related='pnt_product_plastic_tax_id.standard_price',
                                            help='Tasa de impuesto por plástico no reciclable adquirido fuera de España.'
                                                 'Es recuperable si finalmente es vendido fuera de España.')
