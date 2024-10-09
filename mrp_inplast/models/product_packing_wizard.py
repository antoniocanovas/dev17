from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProductPackingWizard(models.TransientModel):
    _name = "product.packing.wizard"
    _description = "Product Packing Wizard"

    name = fields.Many2one("product.template", string="Product")
    bom_template_id = fields.Many2one("product.bom.template", required=True)
    type = fields.Selection(related="bom_template_id.type")
    base_qty = fields.Integer('Base qty')
    box_qty = fields.Integer('Box qty', default=1)

    @api.onchange("type")
    def _get_packing_sufix(self):
        for record in self:
            sufix = "."
            if record.type == "box":
                sufix = ".C" + record.bom_template_id.code
            elif record.type == "pallet":
                sufix = ".P" + record.bom_template_id.code
            record["sufix"] = sufix

    sufix = fields.Char(
        "Sufix", store=True, readonly=False, compute="_get_packing_sufix"
    )

    def create_packing_products(self):
        for record in self:
            # Tipo de empaquetado PALET o Caja:
            # Cantidades base:

            type, sale_ok, purchase_ok =  " - Caja ", False, False
            baseqty, boxqty = record.base_qty, record.box_qty
            packagetype = self.env.ref("product_inplast.package_type_box_inplast")

            if record.type != "box":
                type = " - Palet "
                packagetype = self.env.ref(
                    "product_inplast.package_type_pallet_inplast"
                )
                sale_ok = True
                purchase_ok = True

            # Crear producto:
            dye, code = "", ""
            if record.name.pnt_product_dye:
                dye = " " + record.name.pnt_product_dye

            # Comprobar si el producto ya existía (nombre similar creado automáticamente):
            name = record.name.name + dye + type + str(baseqty)
            exist = self.env["product.template"].search([("name", "=", name)])
            if exist.ids:
                raise UserError("Este producto ya existe.")

            # Asignar un código similar al producto padre pero no repetido:
            if record.name.default_code:
                code = record.name.default_code + record.sufix
                # Desarrollo para que no repita default_code (13/06/24):
                existcode = self.env["product.template"].search(
                    [("default_code", "=", code)]
                )
                if existcode.ids:
                    raise UserError(
                        'Código duplicado, cambia el último campo "Sufix".'
                    )

            # Continuamos, si no existe el producto y default_code es único:
            routemrp = self.env.ref("mrp.route_warehouse0_manufacture")
            newpacking = self.env["product.template"].create(
                {
                    "name": name,
                    "pnt_product_type": "packing",
                    "pnt_parent_id": record.name.id,
                    "pnt_parent_qty": baseqty,
                    "weight": record.name.weight * baseqty,
                    "detailed_type": "product",
                    "default_code": code,
                    "pnt_product_dye": record.name.pnt_product_dye,
                    "list_price": record.name.list_price * baseqty,
                    "ipnr_subject": "yes" if record.name.ipnr_subject else "category",
                    "categ_id": record.name.categ_id.id,
                    "standard_price": record.name.standard_price * baseqty,
                    "sale_ok": sale_ok,
                    "purchase_ok": purchase_ok,
                    "tracking": "lot",
                    "pnt_mrp_as_serial": True,
                    "route_ids": [(6, 0, [routemrp.id])],
                    "pnt_box_qty": boxqty,
                }
            )
            newpacking.write(
                {
                    "plastic_weight_non_recyclable": record.name.plastic_weight_non_recyclable * baseqty,
                    "plastic_tax_weight": record.name.plastic_tax_weight * baseqty,
                    "tax_plastic_type": record.name.tax_plastic_type,
                    "plastic_tax_regime_manufacturer": record.name.plastic_tax_regime_manufacturer,
                    "plastic_type_key": record.name.plastic_type_key,
                    "plastic_tax_regime_acquirer": record.name.plastic_tax_regime_acquirer,
                }
            )

            # Crear lista de materiales
            uom_weight = self.env.ref("uom.product_uom_categ_kgm")
            newldm = self.env["mrp.bom"].create(
                {
                    "code": name,
                    "product_tmpl_id": newpacking.id,
                    "type": "normal",
                    "pnt_raw_type_id": uom_weight.id,
                }
            )

            for li in record.bom_template_id.line_ids:
                newbomboxline = self.env["mrp.bom.line"].create(
                    {
                        "product_id": li.product_id.id,
                        "product_qty": li.quantity,
                        "bom_id": newldm.id,
                    }
                )


            # Incluir materiales desde la ldm de producto base:
            if not record.name.bom_ids.ids:
                raise UserError(
                    "Haz una lista de materiales con componentes o materiales en el producto base "
                    "antes de crear empaquetados."
                )
            else:
                bom = record.name.bom_ids[0]
                for li in bom.bom_line_ids:
                    newbomline = self.env["mrp.bom.line"].create(
                        {
                            "product_id": li.product_id.id,
                            "pnt_raw_percent": li.pnt_raw_percent,
                            "product_qty": li.product_qty * baseqty,
                            "product_uom_id": li.product_uom_id.id,
                            "bom_id": newldm.id,
                        }
                    )


            # Crear en tarifas:
            pricelist = []
            pricelist_item = self.env["product.pricelist.item"].search(
                [("product_tmpl_id", "=", record.name.id)]
            )
            for item in pricelist_item:
                if item.pricelist_id.id not in pricelist:
                    pricelistitem = self.env["product.pricelist.item"].create(
                        {
                            "pricelist_id": item.pricelist_id.id,
                            "product_tmpl_id": newpacking.id,
                            "applied_on": "1_product",
                            "compute_price": "fixed",
                            #'price_surcharge': newpacking.pnt_plastic_1000unit_tax / 1000,
                            "fixed_price": newpacking.list_price,
                        }
                    )
                    pricelist.append(item.pricelist_id.id)

            # Asignar packaging_ids (product.packaging) al nuevo producto del tipo CAJA o PALET para huecos disponibles:
            product = self.env["product.product"].search(
                [("product_tmpl_id", "=", newpacking.id)])[0]
            newpackingtype = self.env["product.packaging"].create(
                {
                    "name": record.type + " " + str(baseqty),
                    "package_type_id": packagetype.id,
                    "product_id": product.id,
                    "product_uom_id": product.uom_id.id,
                    "sales": True,
                    "purchase": True,
                    "qty": 1,
                }
            )
            # Asignar packaging_ids (product.packaging) al producto base para vender por múltiplos:
            product = self.env["product.product"].search(
                [("product_tmpl_id", "=", record.name.id)])[0]

            newpackingtype = self.env["product.packaging"].create(
                {
                    "name": record.type + " " + str(baseqty),
                    "package_type_id": packagetype.id,
                    "product_id": product.id,
                    "product_uom_id": product.uom_id.id,
                    "sales": True,
                    "purchase": True,
                    "qty": baseqty,
                }
            )
