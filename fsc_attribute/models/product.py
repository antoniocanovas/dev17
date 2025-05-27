from odoo import fields, models, api, _

class ProductProduct(models.Model):
    _inherit = 'product.product'

    # Reescribir campo para permitir ver las variantes con un sólo valor:
    product_template_variant_value_ids = fields.Many2many(domain=[], store=True)
    # Campos personalizados para poder agrupar y filtrar por dimensión y acabado:
    fsc_dimension_value_id = fields.Many2one('product.attribute.value', string='Dimension', store=True, compute='_get_fsc_dimension_value_id')
    fsc_quality_value_id = fields.Many2one('product.attribute.value', string='Quality', store=True, compute='_get_fsc_quality_value_id')

    @api.depends('product_tmpl_id.attribute_line_ids')
    def _get_fsc_dimension_value_id(self):
        for rec in self:
            attribute = self.env.company.fsc_dimension_attribute_id
            value = self.env['product.template.attribute.value'].search([
                ('attribute_id', '=', attribute.id),
                ('id', 'in', rec.product_template_variant_value_ids.ids),
            ]).product_attribute_value_id.id
            rec.fsc_dimension_value_id = value

    @api.depends('product_tmpl_id.attribute_line_ids')
    def _get_fsc_quality_value_id(self):
        for rec in self:
            attribute = self.env.company.fsc_quality_attribute_id
            value = self.env['product.template.attribute.value'].search([
                ('attribute_id', '=', attribute.id),
                ('id', 'in', rec.product_template_variant_value_ids.ids),
            ]).product_attribute_value_id.id
            rec.fsc_quality_value_id = value

    """
    (SI) product_template_variant_value_ids en product.product apunta a product.template.attribute.value
    (NO) product_template_attribute_value_ids en product.product apunta a product.template.attribute.value
    """