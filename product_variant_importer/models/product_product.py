# Copyright Serincloud SL - Ingenieriacloud.com


from odoo import fields, models, api

class ProductProduct(models.Model):
    _inherit = "product.product"

    # Pares por variante de producto, se usará en el cálculo de tarifas y líneas de venta:
    def _get_shoes_product_product_pair_count(self):
        for record in self:
            count = 1
            bom = self.env['mrp.bom'].search([('product_id','=',record.id)])
            if bom.ids:
                count = bom[0].pairs_count
            record['pairs_count'] = count
    pairs_count = fields.Integer('Pairs', store=False, compute='_get_shoes_product_product_pair_count')

    # Product assortment (to be printed on sale.order and account.move reports):
    def _get_product_assortment_code(self):
        for record in self:
            assortment_code = ""
            assortment_attribute = self.env.user.company_id.bom_attribute_id

            # El campo en el product.product es product_template_variant_value_ids
            # Este campo es un m2m a product.template.attribute.value
            # Dentro de ese modelo hay un attribute_id que apunta a product_attribute (que ha de ser el de la compañía) y
            # un product_attribute_value_id que apunta a product.attribute.value

            # Si hay varios atributos sería lo siguiente:
            if record.product_template_variant_value_ids.ids:
                ptvv = self.env['product.template.attribute.value'].search(
                    [('id', 'in', record.product_template_variant_value_ids.ids),
                     ('attribute_id', '=', assortment_attribute.id)])
            # Para el caso de una sóla variante en el template el valor del campo es False:
            else:
                ptvv = self.env['product.template.attribute.value'].search(
                    [('product_tmpl_id', '=', record.product_tmpl_id.id),
                     ('attribute_id', '=', assortment_attribute.id)])

            # este modelo tiene un campo que es "set_template_id" que apunta al modelo "set.template"
            # Los valores que nos interesan son las líneas de este último, pero utilizamos el campo code para impresión)
            if ptvv.id:
                assortment_code = ptvv.product_attribute_value_id.set_template_id.code
            record['assortment_code'] = assortment_code
    assortment_code = fields.Char('Assortment', store=False, compute='_get_product_assortment_code')

    color_attribute_id = fields.Many2one('product.attribute.value', string='Color', store=True)
    size_attribute_id = fields.Many2one('product.attribute.value', string='Size', store=True)

    @api.depends('create_date')
    def set_color_and_size(self):
        for record in self:
            size_attribute = self.env.company.size_attribute_id
            color_attribute = self.env.company.color_attribute_id

            size, color, len_size_attribute, len_color_attribute, size_value, color_value = False, False, 0, 0, False, False

            for li in record.product_template_variant_value_ids:
                #  Parámetros de empresa:
                if li.attribute_id.id == size_attribute.id: size_value = li
                if li.attribute_id.id == color_attribute.id: color_value = li

                # Comprobar si sólo hay una variante de color o talla, porque en este caso no se crean product.template.attribute.line:
                pt_attrib_lines = record.product_tmpl_id.attribute_line_ids
                for li in pt_attrib_lines:
                    if li.attribute_id == size_attribute:
                        size_line = li
                        len_size_attribute = len(li.value_ids.ids)
                    if li.attribute_id == color_attribute:
                        color_line = li
                        len_color_attribute = len(li.value_ids.ids)

                # Caso de que haya un un sólo color o talla en la plantilla, asignación:
                if len_size_attribute == 1:
                    size_value = size_line.value_ids[0].id
                if len_color_attribute == 1:
                    color_value = color_line.value_ids[0].id

                # Casos de que haya varios colores o tallas en la plantilla de producto:
                if len_size_attribute > 1:
                    # Para buscar la talla:
                    size_value = self.env['product.template.attribute.value'].search([
                        ('product_tmpl_id', '=', record.product_tmpl_id.id),
                        ('id', 'in', record.product_template_variant_value_ids.ids),
                        ('attribute_id', '=', size_attribute.id)
                    ]).product_attribute_value_id.id

                if len_color_attribute > 1:
                    # Para buscar el color:
                    color_value = self.env['product.template.attribute.value'].search([
                        ('product_tmpl_id', '=', record.product_tmpl_id.id),
                        ('id', 'in', record.product_template_variant_value_ids.ids),
                        ('attribute_id', '=', color_attribute.id)
                    ]).product_attribute_value_id.id

                record.write({'size_attribute_id': size_value, 'color_attribute_id': color_value})