from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class SectionRel(models.Model):
    _name = 'sale.order.multisections.rel'
    _description = 'Sections Relations'

    name = fields.Char('Name')
    child_section_id = fields.Many2one(
        'sale.order.line'
    )
    parent_section_id = fields.Many2one(
       'sale.order.line'
    )