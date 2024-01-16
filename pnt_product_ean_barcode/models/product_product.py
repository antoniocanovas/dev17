# Copyright Puntsistemes.es


from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from gtin import GTIN

class ProductProduct(models.Model):
    _inherit = "product.product"

    pnt_ean_required = fields.Boolean(string="EAN required", related="categ_id.pnt_ean_required")

    def create_default_code(self):
        code = self.env.context.get('code')
        seq = self.env["ir.sequence"].search([("code", "=", code)],
                                             limit=1)
        pnt_ean14_prefix = seq.pnt_ean14_prefix

        for product in self:
            barcode = str(product.barcode)
            if not product.barcode:
                barcode = self.env["ir.sequence"].next_by_code(code)
            if len(barcode) == 12:
                if pnt_ean14_prefix:
                    barcode = (str(pnt_ean14_prefix) + str(barcode) +
                               str(GTIN(raw=str(barcode)).check_digit))
                    super(ProductProduct, self).write({"barcode": barcode})
                else:
                    barcode = str(barcode) + str(
                        GTIN(raw=str(barcode)).check_digit)
                    super(ProductProduct, self).write({"barcode": barcode})
            else:
                raise UserError(
                    _("The product %s does not have an EAN length") % product.display_name)

