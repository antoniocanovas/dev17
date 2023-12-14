# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api, _

class SsaleOrder(models.Model):
    _inherit = 'sale.order'

    is_wp = fields.Boolean('Watio Pico')
    wp_power = fields.Float('Power Kw', store=True)
    wp_template_id = fields.Many2one('wp.template', string='WP Template', store=True)



    wp_pico = fields.Float('Watio pico', store=True, readonly=False)
    wp_hour = fields.Float('Watio hora', store=True, readonly=False)
    wp_margin = fields.Float('WP Margin', store=True, readonly=False)
    wp_charger_margin =  fields.Float('Charger Margin', store=True, readonly=False)

    @api.onchange('wp_template_id')
    def get_wp_template_lines(self):
        for record in self:
            record.wp_line_ids.unlink()
            record.write({'wp_pico': record.wp_template_id.wp_pico,
                          'wp_hour': record.wp_template_id.wp_hour,
                          'wp_margin': record.wp_template_id.wp_margin,
                          'wp_charger_margin': record.wp_template_id.wp_charger_margin,
                          })

    @api.onchange('wp_template_id')
    def get_wp_template_lines(self):
        for record in self:
            wplines = []
            for li in record.wp_template_id.line_ids:
                newline = self.env['wp.sale.line'].create({'product_id':li.product_id.id,
                                                           'name':li.name,
                                                           'quantity':li.quantity,
                                                           'factor':li.factor,
                                                           'subtotal':0})
                wplines.append(newline.id)
            record['wp_line_ids'] = [(6,0,wplines)]
    wp_line_ids = fields.One2many('wp.sale.line', 'sale_id', string='WP Lines', compute='get_wp_template_lines')

    @api.onchange('wp_pico','wp_hour','wp_margin','wp_charger_margin','wp_line_ids','wp_power')
    def _update_wp_prices(self):
        total = 0
        for li in self.wp_line_ids:
            # Case watio-pico:
            if li.product_id.wp_type == 'wp':
                subtotal = self.wp_power * 1000 * li.factor * self.wp_pico * (1 + self.wp_margin/100)
            # Case watio-hour:
            elif li.product_id.wp_type == 'wh':
                subtotal = self.wp_power * 1000 * li.factor * self.wp_hour * (1 + self.wp_margin/100)
            # Case charger:
            else:
                subtotal = li.product_id.standard_price * (1 + self.wp_charger_margin/100)
            li.subtotal = subtotal
            total += subtotal
        self.wp_subtotal = total

    def update_wp_sale_order(self):
        self.order_line.unlink()
        for li in self.wp_line_ids:
            newline = self.env['sale.order.line'].create({'product_id': li.product_id.id,
                                                          'name': li.name,
                                                          'product_uom_qty': li.quantity,
                                                          'price_unit': li.subtotal / li.quantity,
                                                          'order_id': self.id})

    @api.onchange('write_date')
    def _get_wp_subtotal(self):
        subtotal = 0
        for li in self.wp_line_ids:
            subtotal += li.subtotal
        self.wp_subtotal = subtotal
    wp_subtotal = fields.Monetary('Subtotal', store=False, compute='_get_wp_subtotal')

    def action_open_wp_sale_wizard(self):
        return {
            'name': _("WP Wizard"),
            'view_mode': 'form',
            'view_id': self.env.ref('watio_pico.pnt_wp_sale_order_wizard').id,
            'view_type': 'form',
            'res_model': 'wp.product.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            # 'domain': '[if you need]',
            'context': {'pnt_sale_id': self.id, }
        }

