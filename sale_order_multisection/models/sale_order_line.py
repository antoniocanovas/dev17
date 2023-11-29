from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    partner_id = fields.Many2one('res.partner', related='order_id.partner_id', readonly=True)
    tax_country_id = fields.Many2one('res.country', related='order_id.tax_country_id', readonly=True)
    pricelist_id = fields.Many2one('product.pricelist', related='order_id.pricelist_id', readonly=True)
    section_line_ids = fields.One2many('sale.order.line', 'section_id', store=True, string='Section Lines')

    section = fields.Char('Section', store=True, readonly=True)

    section_id = fields.Many2one('sale.order.line', store=True, readonly=True)
    new_section_id = fields.Many2one('sale.order.line', store=True, readonly=False)

    # Reports hidden price line fields:
    print_mode_section  = fields.Selection([('hide_price','Hide line prices'),
                                            ('executive','Executive'),
                                            ('hide_subtotal', 'Hide section subtotals'),
                                            ('hide_subtotal_and_price', 'Hide subtotal and prices'),],
                                           string='Print format')

    print_mode_line     = fields.Selection(related='section_id.print_mode_section')

    hide_subtotal_section   = fields.Boolean('Hide subtotal', store=True, readonly=False)
    hide_subtotal_line      = fields.Boolean('Hide price', store=False, related='section_id.hide_subtotal_section')
    ms_sequence = fields.Char('Field to order', store=True)

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

    #    @api.depends('create_date')
    def _get_total_section(self):
        for record in self:
            total = 0
            if record.display_type == 'line_section':
                secciones = record.child_ids.ids
                secciones.append(record.id)
                lineas = self.env['sale.order.line'].search([('section_id', 'in', secciones)])
                for li in lineas: total += li.price_subtotal
            record['section_total'] = total
    section_total = fields.Float('Total Section', readonly=True,compute=_get_total_section, store=False)

    @api.constrains('name')
    def _avoid_duplicated_sections(self):
        for record in self:
            if (record.display_type == 'line_section') and (record.name[:1] == record.order_id.multisection_key):
                section_code = record.name.split()[0]
                line_ids = self.env['sale.order.line'].search([('order_id','=',record.order_id.id),('display_type','=','line_section'),('section','!=',False),('id','!=',record.id)])
                if line_ids.ids:
                    for li in line_ids:
                        if section_code == li.section: raise UserError('Duplicated section name ' + section_code + ' !!!')


    def resequence_in_o2m_new_sol(self):
        # Review Sequence for new lines created from o2m sections buttom (by default would be the last and must be in record section):
        for record in self:
            if record.ms_review:
                seq = record.section_id.sequence
                lines = self.env['sale.order.line'].search([('section_id', '=', record.section_id.id), ('id', '!=', record.id),
                                                            ('create_date', '<', record.create_date)])
                if lines:
                    lines_sorted = lines.sorted(key=lambda r: (r.sequence))
                    seq = self.env['sale.order.line'].search([('id', '=', lines_sorted.ids.pop())]).sequence
                record.write({'sequence': seq, 'ms_review': False})