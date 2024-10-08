# Copyright 2023 Serincloud SL - Ingenieriacloud.com


from odoo import api, fields, models, tools, _
from odoo.tools.misc import unique


class ProductProduct(models.Model):
    _inherit = "product.product"

    # Reescribimos la función estandar para poder añadir el dye como parámetro
    @api.depends('name', 'default_code', 'product_tmpl_id', 'pnt_product_dye')
    @api.depends_context('display_default_code', 'seller_id', 'company_id',
                         'partner_id')
    def _compute_display_name(self):

        def get_display_name(name, code, dye):
            if self._context.get('display_default_code', True) and code and dye:
                    return f'[{code}] {name} {dye}'
            elif self._context.get('display_default_code', True) and code and not dye:
                return f'[{code}] {name}'
            elif dye:
                return f'{name} {dye}'
            return name

        partner_id = self._context.get('partner_id')
        if partner_id:
            partner_ids = [partner_id, self.env['res.partner'].browse(
                partner_id).commercial_partner_id.id]
        else:
            partner_ids = []
        company_id = self.env.context.get('company_id')

        # all user don't have access to seller and partner
        # check access and use superuser
        self.check_access_rights("read")
        self.check_access_rule("read")

        product_template_ids = self.sudo().product_tmpl_id.ids

        if partner_ids:
            # prefetch the fields used by the `display_name`
            supplier_info = self.env['product.supplierinfo'].sudo().search_fetch(
                [('product_tmpl_id', 'in', product_template_ids),
                 ('partner_id', 'in', partner_ids)],
                ['product_tmpl_id', 'product_id', 'company_id', 'product_name',
                 'product_code'],
            )
            supplier_info_by_template = {}
            for r in supplier_info:
                supplier_info_by_template.setdefault(r.product_tmpl_id, []).append(r)

        for product in self.sudo():
            variant = product.product_template_attribute_value_ids._get_combination_name()

            name = variant and "%s (%s)" % (product.name, variant) or product.name
            sellers = self.env['product.supplierinfo'].sudo().browse(
                self.env.context.get('seller_id')) or []
            if not sellers and partner_ids:
                product_supplier_info = supplier_info_by_template.get(
                    product.product_tmpl_id, [])
                sellers = [x for x in product_supplier_info if
                           x.product_id and x.product_id == product]
                if not sellers:
                    sellers = [x for x in product_supplier_info if not x.product_id]
                # Filter out sellers based on the company. This is done afterwards for a better
                # code readability. At this point, only a few sellers should remain, so it should
                # not be a performance issue.
                if company_id:
                    sellers = [x for x in sellers if
                               x.company_id.id in [company_id, False]]
            if sellers:
                temp = []
                for s in sellers:
                    seller_variant = s.product_name and (
                            variant and "%s (%s)" % (
                    s.product_name, variant) or s.product_name
                    ) or False
                    temp.append(get_display_name(seller_variant or name,
                                                 s.product_code or product.default_code,
                                                 product.pnt_product_dye if product.pnt_product_dye else False))

                # => Feature drop here, one record can only have one display_name now, instead separate with `,`
                # Remove this comment
                product.display_name = ", ".join(unique(temp))
            else:
                product.display_name = get_display_name(name, product.default_code,
                                                        product.pnt_product_dye if product.pnt_product_dye else False)