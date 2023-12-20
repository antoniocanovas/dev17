from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'


    pnt_pricelist_mode   = fields.Selection([('auto','Automático'),
                                             ('bom', 'Escandallo general'),
                                             ('custom', 'Escandallo personalizado')],
                                            store=True, copy=True, string='Pricelist mode')

    pnt_pricelist_update = fields.Selection([('1m', 'Monthly'),
                                             ('3m', 'Quarter'),
                                             ('6m', '6 months'),
                                             ('custom', 'Negociación')],
                                            store=True, copy=True, string='Pricelist update')
