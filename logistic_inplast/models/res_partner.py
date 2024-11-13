from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    container_id = fields.Many2one('container.type', string="Main")
    container_ids = fields.Many2many('container.type', string="Others")