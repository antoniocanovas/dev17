
from odoo import _, api, fields, models

class WpSaleOrderWizard(models.TransientModel):
    _name = 'wp.sale.order.wizard'
    _description = 'WP Wizard'

    sale_id = fields.Many2one(
        'sale.order',
        string="Sale order",
    )
    wp_template_id = fields.Many2one('wp.template', string="WP Template")

    def process(self):
        self.ensure_one()
        for record in self:
            sale = record.sale_id
            sale.wp_line_ids.unlink()
            sale.write({'wp_pico': record.wp_template_id.wp_pico,
                        'wp_hour': record.wp_template_id.wp_hour,
                        'wp_margin': record.wp_template_id.wp_margin,
                        'wp_charger_margin': record.wp_template_id.wp_charger_margin,
                        })
            for li in record.wp_template_id.line_ids:
                newline = self.env['wp.sale.line'].create({'product_id':li.product_id.id,
                                                           'name':li.name,
                                                           'quantity':li.quantity,
                                                           'factor':li.factor,
                                                           'subtotal':0,
                                                           'sale_id':record.sale_id.id})
