from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    partner_id = fields.Many2one('res.partner', related='order_id.partner_id', readonly=True)
    pricelist_id = fields.Many2one('product.pricelist', related='order_id.pricelist_id', readonly=True)
    section_line_ids = fields.One2many('sale.order.line', 'section_id', store=True, string='Section Lines')

    section = fields.Char('Section', readonly=True)
    section_id = fields.Many2one('sale.order.line', readonly=True)

    # Reports hidden price line fields:
    print_mode_section  = fields.Selection([('hide_price','Hide line prices'),
                                            ('executive','Executive'),
                                            ('hide_subtotal', 'Hide section subtotals'),
                                            ('hide_subtotal_and_price', 'Hide subtotal and prices'),],
                                           string='Print format')

    print_mode_line     = fields.Selection(related='section_id.print_mode_section')

    hide_subtotal_section   = fields.Boolean('Hide subtotal', store=True, readonly=False)
    hide_subtotal_line      = fields.Boolean('Hide price', store=False, related='section_id.hide_subtotal_section')

    level = fields.Integer(
        'Level',
        readonly=True,
    )
    child_ids = fields.Many2many(
        'sale.order.line',
        relation='sale_order_multisections_rel',
        column1='parent_section_id',
        column2='child_section_id',
        readonly=True,
    )

    parent_ids = fields.Many2many(
        'sale.order.line',
        relation='sale_order_multisections_rel',
        column1='child_section_id',
        column2='parent_section_id',
        readonly=True,
    )

    ms_review = fields.Boolean('Review')

    @api.depends('create_date')
    def _get_total_section(self):
        for record in self:
            total = 0
            if record.display_type == 'line_section':
                secciones = record.child_ids.ids
                secciones.append(record.id)
                lineas = self.env['sale.order.line'].search([('section_id', 'in', secciones)])
                for li in lineas: total += li.price_subtotal
            record['section_total'] = total

    section_total = fields.Float(
        'Total Section',
        readonly=True,
        compute=_get_total_section,
    )




