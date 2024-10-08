from odoo import _, api, fields, models
from odoo.exceptions import UserError
from pkg_resources import require


class ProductPackingWizard(models.TransientModel):
    _name = "product.packing.wizard"
    _description = "Product Packing Wizard"

    # Campos generales
    name = fields.Many2one("product.template", string="Product")
    bom_template_id = fields.Many2one("product.bom.template", required=1)
    pnt_type = fields.Selection(related="bom_template_id.pnt_type")
    # Cajas:

    pnt_box_type_id = fields.Many2one(related="bom_template_id.pnt_box_type_id")
    pnt_box_base_qty = fields.Integer("Base qty")
    pnt_box_bag_id = fields.Many2one(related="bom_template_id.pnt_box_bag_id")
    pnt_box_bag_qty = fields.Integer(related="bom_template_id.pnt_box_bag_qty")
    pnt_box_label_id = fields.Many2one(related="bom_template_id.pnt_box_label_id")
    pnt_box_label_qty = fields.Integer(related="bom_template_id.pnt_box_label_qty")
    pnt_box_seal_id = fields.Many2one(related="bom_template_id.pnt_box_seal_id")
    pnt_box_seal_qty = fields.Integer(related="bom_template_id.pnt_box_seal_qty")

    # Palets:
    pnt_pallet_type_id = fields.Many2one(related="bom_template_id.pnt_pallet_type_id")
    pnt_pallet_qty = fields.Integer(related="bom_template_id.pnt_pallet_qty")
    pnt_pallet_box_id = fields.Many2one(related="bom_template_id.pnt_pallet_box_id")
    pnt_pallet_box_qty = fields.Integer(related="bom_template_id.pnt_pallet_box_qty")
    pnt_pallet_base_qty = fields.Integer(
        "Base qty", store=True, readonly=False, compute="_get_pallet_base_qty"
    )
    pnt_pallet_film_id = fields.Many2one(related="bom_template_id.pnt_pallet_film_id")
    pnt_pallet_film_qty = fields.Integer(related="bom_template_id.pnt_pallet_film_qty")
    pnt_pallet_seal_id = fields.Many2one(related="bom_template_id.pnt_pallet_seal_id")
    pnt_pallet_seal_qty = fields.Integer(related="bom_template_id.pnt_pallet_seal_qty")
    pnt_pallet_label_id = fields.Many2one(related="bom_template_id.pnt_pallet_label_id")
    pnt_pallet_label_qty = fields.Integer(
        related="bom_template_id.pnt_pallet_label_qty"
    )
    pnt_picking_label_id = fields.Many2one(
        related="bom_template_id.pnt_picking_label_id"
    )
    pnt_picking_label_qty = fields.Integer(
        related="bom_template_id.pnt_picking_label_qty"
    )

    @api.onchange("pnt_type")
    def _get_packing_prefix(self):
        for record in self:
            if record.pnt_type == "box":
                prefix = "C."
            else:
                prefix = "P."
            record["pnt_prefix"] = prefix

    pnt_prefix = fields.Char(
        "Prefix", store=True, readonly=False, compute="_get_packing_prefix"
    )

    @api.depends("pnt_pallet_box_qty", "pnt_pallet_box_id")
    def _get_pallet_base_qty(self):
        for record in self:
            qty = 0
            if record.pnt_type == "pallet":
                qty = (
                    record.pnt_pallet_box_qty * record.pnt_pallet_box_id.pnt_parent_qty
                )
            record["pnt_pallet_base_qty"] = qty

    def create_packing_products(self):
        for record in self:
            # Tipo de empaquetado PALET o Caja:
            # Cantidades base:

            baseqty, boxqty, type, sale_ok, purchase_ok = (
                record.pnt_box_base_qty,
                1,
                " - Caja ",
                False,
                False,
            )

            packagetype = self.env.ref("product_inplast.package_type_box_inplast")
            if record.pnt_type != "box":
                boxqty = record.pnt_pallet_box_qty
                baseqty = record.pnt_pallet_base_qty
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
                code = record.pnt_prefix + record.name.default_code
                # Desarrollo para que no repita default_code (13/06/24):
                existcode = self.env["product.template"].search(
                    [("default_code", "=", code)]
                )
                if existcode.ids:
                    raise UserError(
                        'Código duplicado, cambia el último campo "Prefix".'
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
                    "plastic_weight_non_recyclable": record.name.plastic_weight_non_recyclable
                    * baseqty,
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

#### Nueva versión:
            for li in record.bom_template_id.line_ids:
                newbomboxline = self.env["mrp.bom.line"].create(
                    {
                        "product_id": li.product_id.id,
                        "product_qty": li.quantity,
                        "bom_id": newldm.id,
                    }
                )


### Desde aquí lo que hay que revisar:

            """

            # Crear componentes de la lista de materiales para CAJAS:
            if record.pnt_type == "box":
                product = self.env["product.product"].search(
                    [("product_tmpl_id", "=", record.name.id)]
                )
                newbomboxline = self.env["mrp.bom.line"].create(
                    {
                        "product_id": product.id,
                        "product_qty": record.pnt_box_base_qty,
                        "bom_id": newldm.id,
                    }
                )
                boxproduct = self.env["product.product"].search(
                    [("product_tmpl_id", "=", record.pnt_box_type_id.id)]
                )[0]
                newbomboxline = self.env["mrp.bom.line"].create(
                    {"product_id": boxproduct.id, "product_qty": 1, "bom_id": newldm.id}
                )
                bag = self.env["product.product"].search(
                    [("product_tmpl_id", "=", record.pnt_box_bag_id.id)]
                )[0]
                newbomboxbag = self.env["mrp.bom.line"].create(
                    {
                        "product_id": bag.id,
                        "product_qty": record.pnt_box_bag_qty,
                        "bom_id": newldm.id,
                    }
                )
                label = self.env["product.product"].search(
                    [("product_tmpl_id", "=", record.pnt_box_label_id.id)]
                )[0]
                newbomboxlabel = self.env["mrp.bom.line"].create(
                    {
                        "product_id": label.id,
                        "product_qty": record.pnt_box_label_qty,
                        "bom_id": newldm.id,
                    }
                )
                seal = self.env["product.product"].search(
                    [("product_tmpl_id", "=", record.pnt_box_seal_id.id)]
                )[0]
                newbomboxseal = self.env["mrp.bom.line"].create(
                    {
                        "product_id": seal.id,
                        "product_qty": record.pnt_box_seal_qty,
                        "bom_id": newldm.id,
                    }
                )

            # Crear componentes de la lista de materiales para los PALETS:
            else:
                product = self.env["product.product"].search(
                    [("product_tmpl_id", "=", record.pnt_pallet_type_id.id)]
                )[0]
                newbompalletline = self.env["mrp.bom.line"].create(
                    {
                        "product_id": product.id,
                        "product_qty": record.pnt_pallet_qty,
                        "bom_id": newldm.id,
                    }
                )
                box = self.env["product.product"].search(
                    [("product_tmpl_id", "=", record.pnt_pallet_box_id.id)]
                )[0]
                newbompalletline = self.env["mrp.bom.line"].create(
                    {
                        "product_id": box.id,
                        "product_qty": record.pnt_pallet_box_qty,
                        "bom_id": newldm.id,
                    }
                )
                film = self.env["product.product"].search(
                    [("product_tmpl_id", "=", record.pnt_pallet_film_id.id)]
                )[0]
                newbompalletfilm = self.env["mrp.bom.line"].create(
                    {
                        "product_id": film.id,
                        "product_qty": record.pnt_pallet_film_qty,
                        "bom_id": newldm.id,
                    }
                )
                seal = self.env["product.product"].search(
                    [("product_tmpl_id", "=", record.pnt_pallet_seal_id.id)]
                )[0]
                newbompalletseal = self.env["mrp.bom.line"].create(
                    {
                        "product_id": seal.id,
                        "product_qty": record.pnt_pallet_seal_qty,
                        "bom_id": newldm.id,
                    }
                )

                label = self.env["product.product"].search(
                    [("product_tmpl_id", "=", record.pnt_pallet_label_id.id)]
                )[0]
                newbompalletlabel = self.env["mrp.bom.line"].create(
                    {
                        "product_id": label.id,
                        "product_qty": record.pnt_box_label_qty,
                        "bom_id": newldm.id,
                    }
                )
                pickinglabel = self.env["product.product"].search(
                    [("product_tmpl_id", "=", record.pnt_picking_label_id.id)]
                )[0]
                newbompalletlabel = self.env["mrp.bom.line"].create(
                    {
                        "product_id": pickinglabel.id,
                        "product_qty": record.pnt_picking_label_qty,
                        "bom_id": newldm.id,
                    }
                )

                # En caso de pallets por materiales hay que añadir las bolsas de los tapones y los materiales base:
                if record.pnt_type == "palletmat":
                    palletboxbag = self.env["product.product"].search(
                        [("product_tmpl_id", "=", record.pnt_box_bag_id.id)]
                    )[0]
                    newbompalletboxbag = self.env["mrp.bom.line"].create(
                        {
                            "product_id": palletboxbag.id,
                            "product_qty": record.pnt_box_bag_qty,
                            "bom_id": newldm.id,
                        }
                    )

                    if not record.name.bom_ids.ids:
                        raise UserError(
                            "Haz una lista de materiales con componentes o materiales en el producto base "
                            "antes de usar este tipo de empaquetado."
                        )
                    else:
                        bom = record.name.bom_ids[0]
                        for li in bom.bom_line_ids:
                            newbomline = self.env["mrp.bom.line"].create(
                                {
                                    "product_id": li.product_id.id,
                                    "pnt_raw_percent": li.pnt_raw_percent,
                                    "product_qty": li.product_qty
                                    * record.pnt_pallet_base_qty,
                                    "product_uom_id": li.product_uom_id.id,
                                    "bom_id": newldm.id,
                                }
                            )
"""
#### Hasta aquí lo que hay que revisar.
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
                [("product_tmpl_id", "=", newpacking.id)]
            )[0]
            newpackingtype = self.env["product.packaging"].create(
                {
                    "name": record.pnt_type + " " + str(baseqty),
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
                [("product_tmpl_id", "=", record.name.id)]
            )[0]
            if record.pnt_type == "box":
                qty = record.pnt_box_base_qty
            else:
                qty = record.pnt_pallet_base_qty
            newpackingtype = self.env["product.packaging"].create(
                {
                    "name": record.pnt_type + " " + str(baseqty),
                    "package_type_id": packagetype.id,
                    "product_id": product.id,
                    "product_uom_id": product.uom_id.id,
                    "sales": True,
                    "purchase": True,
                    "qty": qty,
                }
            )
