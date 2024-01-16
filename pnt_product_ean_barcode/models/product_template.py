# Copyright puntsistemes.es


from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from gtin import GTIN

class ProductTemplate(models.Model):
    _inherit = ["product.template"]

    pnt_ean_required = fields.Boolean(string="EAN required",
                                      related="categ_id.pnt_ean_required")

    def calc_check_digit(number):

        """El cálculo del dígito se realiza con el siguiente proceso:
        Sumamos todos los dígitos que ocupan las posiciones pares: 8+1+5+4+1+5 = 24 (pares)
        Sumamos todos los digitos que ocupan las posiciones impares: 4+2+8+5+2+4 = 25 (impares)
        Multiplicamos por 3 el valor obtenido en la suma de los dígitos impares: 25*3 = 75
        Sumamos al valor obtenido anteriormente,  la suma de los numeros pares: 24+ 75 = 99
        Redondeamos el valor obtenido a la decena inmediatamante superior, en este caso 100
        El dígito de control es el valor obtenido del redondeo de decenas menos la suma total del punto 4: 100 – 99 = 1."""
        return str((10 - sum((3, 1)[i % 2] * int(n)
                             for i, n in enumerate(reversed(number)))) % 10)

    def validate(number):
        if not isdigits(number):
            raise UserError(_("The perfix can only have numbers"))
        if len(number) not in (14, 13, 12, 8):
            raise UserError(_("EAN code lenght not valid"))
        if calc_check_digit(number[:-1]) != number[-1]:
            raise UserError(_("EAN code control not valid"))
        return number

    def is_valid(number):
        try:
            return bool(validate(number))
        except ValidationError:
            return False

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
                    super(ProductTemplate, self).write({"barcode": barcode})
                else:
                    barcode = str(barcode) + str(
                        GTIN(raw=str(barcode)).check_digit)
                    super(ProductTemplate, self).write({"barcode": barcode})
            else:
                raise UserError(
                    _("The product %s does not have an EAN length") % product.display_name)

    #@api.model_create_multi
     #def create(self, vals_list):
     #   products = super(ProductProduct, self).create(vals_list)
     #   for product in products:
     #       #x.pnt_control_stock = x.product_tmpl_id.pnt_control_stock
     #       #x.pnt_stock_web = x.product_tmpl_id.pnt_stock_web
     #       if product.categ_id.pnt_ean_required:
     #           product.create_default_code()

    #    return products

    #def write(self, values):
    #    res = super(ProductTemplate, self).write(values)
    #    if values.get("barcode"):
    #        for record in self.filtered(lambda r: r.categ_id.pnt_ean_required):
    #            record.create_default_code()

    #    return res

