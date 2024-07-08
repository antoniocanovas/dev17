from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class SaleOrderSets(models.Model):
    _inherit = 'sale.order'

    @api.depends('partner_id')
    def get_key(self):
        for record in self:
            key = "$"
            reg = self.env['ir.config_parameter'].sudo().search([('key', '=', 'multisection_key')])
            if reg.id: key = reg.value
            if record.multisection_key: key = record.multisection_key
            record['multisection_key'] = key

    multisection_key = fields.Char('Multisection Key', compute=get_key, readonly=False, required=True)

    def _get_lines_count(self):
        for record in self:
            total = 0
            results = self.env['sale.order.line'].search([
                ('order_id', '=', record.id),
                ('display_type', '=', 'line_section')])
            if results: total = len(results)
            record['section_line_count'] = total

    section_line_count = fields.Integer('Lines', compute=_get_lines_count)

    def action_view_sections(self):
        action = self.env.ref(
            'sale_order_multisection.action_view_sections').read()[0]
        return action

    def order_sections(self):
        # Reorder sections and lines by section:
        sections = self.env['sale.order.line'].search(
            [('order_id', '=', self.id), ('display_type', '=', 'line_section')]).sorted(key=lambda r: r.section)
        lineas, counter = [], 0
        # Previous lines with no section:
        lines_no_section = self.env['sale.order.line'].search(
            [('order_id', '=', self.id), ('section_id', '=', False), ('display_type', '!=', 'line_section')])
        for li in lines_no_section:
            if li.sequence > counter: counter = li.sequence
        counter = counter + 1
        # Ordering sections:
        for se in sections:
            for li in self.order_line:
                if (li.id == se.id) or (li.section_id.id == se.id):
                    lineas.append(li)
        # New sequence to array lines:
        for li in lineas:
            li['sequence'] = counter
            counter += 1

