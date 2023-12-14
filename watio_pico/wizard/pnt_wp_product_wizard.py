
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class WpProductWizard(models.TransientModel):
    _name = 'wp.product.wizard'
    _description = 'WP Wizard'

    pnt_product_tmpl_id = fields.Many2one(
        'product.template',
        string="Template",
    )
    pnt_wp_template_id = fields.Many2one('wp.template', string="WP Template")

    def process(self):
        self.ensure_one()

        for record in self:
            record.wp_line_ids.unlink()
            record.write({'wp_pico': record.wp_template_id.wp_pico,
                          'wp_hour': record.wp_template_id.wp_hour,
                          'wp_margin': record.wp_template_id.wp_margin,
                          'wp_charger_margin': record.wp_template_id.wp_charger_margin,
                          })

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