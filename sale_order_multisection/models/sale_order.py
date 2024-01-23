from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class SaleOrderSets(models.Model):
    _inherit = 'sale.order'

    enable_multisection = fields.Boolean('Enable multisection')

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

    def update_multisection(self):
        for record in self:
            # 1. Sólo para ofertas en borrador con secciones:
            section_ids = self.env['sale.order.line'].search([('order_id', '=', record.id), ('display_type', '=', 'line_section')])
            if (section_ids) and (record.state in ['draft','sent']):
                line_ids = record.order_line.sorted(key=lambda r: r.sequence)
                section_id, i = 0, 1

                # Set field 'section' in section_lines and 'section_id' in others, ordered by sequence:
                for li in section_ids:
                    section_id = li.id
                    section_code = str(li.sequence)
                    if (li.name[:1] == record.multisection_key):
                        section_code = (li.name.split()[0] + "               ")[:15]
                    li.write({'section': section_code})

                # Preparar ms_sequence para resecuenciar después:
                section_id = False
                for li in line_ids:
                    if li.display_type == 'line_section':
                        section_id = li
                        seq = li.sequence + 10000
                        ms_sequence = li.section + str(seq)
                        li.write({'ms_sequence': ms_sequence, 'section_id': False})
                    else:
                        if (li.new_section_id.id):
                            value = li.new_section_id.id
                            seq = li.sequence + 10000
                            ms_sequence = li.new_section_id.section + str(seq)
                        elif (section_id) and not (li.new_section_id.id):
                            value = section_id.id
                            seq = li.sequence + 10000
                            ms_sequence = section_id.section + str(seq)
                        else:
                            value = False
                            seq = li.sequence + 10000
                            ms_sequence = " " + str(seq)
                        li.write({'section_id': value, 'ms_sequence': ms_sequence})

                # Reordenar secuencias para líneas de new_section_id:
                lines = record.order_line.sorted(key=lambda r: r.ms_sequence)
                for li in lines:
                    li.write({'sequence': i, 'new_section_id': False})
                    i += 1

                # Cálculo de 'parent_ids', 'child_ids' y 'level' por sección, si hay multinivel ($ o multisection_key):
                # NOTA.- Las referencias ".split()[0]" es para quitar los espacios añadidos anteriormente en 'codigo'.
                section_ids = self.env['sale.order.line'].search([('order_id', '=', record.id), ('display_type', '=', 'line_section')])
                for se in section_ids:
                    parents, children, level = [], [], 1
                    line_ids = self.env['sale.order.line'].search(
                        [('order_id', '=', record.id), ('display_type', '=', 'line_section'), ('id', '!=', se.id)])
                    if (se.name[:1] == record.multisection_key):
                        for li in line_ids:
                            lenght_line = len(li.section.split()[0])
                            if (li.section.split()[0] == se.section.split()[0][:lenght_line]):
                                parents.append(li.id)
                                level = len(parents) + 1
                            lenght_section = len(se.section.split()[0])
                            if (se.section.split()[0] == li.section.split()[0][:lenght_section]):
                                children.append(li.id)
                    se.write({'parent_ids': [(6, 0, parents)], 'child_ids': [(6, 0, children)], 'level': level})

    def sort_ms_alphabetic_product_lines(self):
        for record in self:
            record.update_multisection()
            all_line_ids = record.order_line.sorted(key=lambda r: r.sequence)
            o, section = 1, 0
            # Alphabetic order CAPS first, lowers later:
            for li in all_line_ids:
                if (li.display_type != 'line_section') and (section == 0):
                    li.write({'sequence': o})
                    o += 1
                if (li.display_type == 'line_section'):
                    li.write({'sequence': o})
                    o += 1
                    section = li.id
                    line_alphabetic_ids = self.env['sale.order.line']. \
                        search([('order_id','=',record.id),
                                ('section_id','=',section),
                                ('display_type','!=','line_section')]).sorted(key=lambda r: (r.name))
                    for li2 in line_alphabetic_ids:
                        li2.write({'sequence': o})
                        o += 1
