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

    wp_line_ids = fields.One2many('wp.sale.line', 'sale_id', string='WP Lines')

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
