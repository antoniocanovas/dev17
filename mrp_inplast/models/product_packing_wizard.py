from odoo import fields, models
from odoo.exceptions import UserError


class ProductPackingWizard(models.TransientModel):
    _name = "product.packing.wizard"
    _description = "Product Packing Wizard"

    name = fields.Many2one("product.template", string="Product")
    bom_template_id = fields.Many2one("product.bom.template", required=True)
    type = fields.Selection(related="bom_template_id.type")
    base_qty = fields.Integer("Base qty")
    box_qty = fields.Integer("Box qty", default=1)
    partner_ids = fields.Many2many("res.partner", string="Customers", required=True)

    sufix = fields.Char("Sufix", related="bom_template_id.code")

    def _recompute_created_packing_weight(self, packing: models.Model) -> None:
        for product in packing:
            if product.pnt_parent_id and product.pnt_product_type == "packing":
                product.bom_ids._get_product_raw_qty()
                self.env.flush_all()
                product._compute_weight()

    def create_pallet_and_box_products(self) -> None:
        """
        Comprobamos que el producto es de tipo palet y que tiene un producto tipo caja
        en su lista de materiales.
        Si el producto es pallet, buscamos la caja de su lista de materiales y la
        pasamos al método create_packing_products.
        Cuando tenemos la caja procedemos a crear el pallet.
        """
        for record in self:
            template = record.bom_template_id
            template_box = template.box_template_id
            if not template_box:
                raise UserError("El producto seleccionado no plantilla de caja ")

            box_default_code = (
                record.name.default_code + template_box.code
                if record.name.default_code and template_box.code
                else None
            )
            if box_default_code:
                domain = [
                    ("default_code", "=", box_default_code),
                ]
            else:
                domain = [
                    ("name", "=", record.name.name + " - " + template_box.printed_code),
                    ("pnt_parent_id", "=", record.name.id),
                    ("pnt_parent_qty", "=", record.base_qty),
                    ("pnt_box_qty", "=", record.box_qty),
                ]

            exist = self.env["product.template"].search(domain)
            if not exist.ids:
                # PASO 1: Crear la CAJA usando el box_template_id
                box_wizard = self.create(
                    {
                        "name": record.name.id,
                        "bom_template_id": template_box.id,
                        "base_qty": record.base_qty / record.box_qty,
                        "box_qty": 1,
                        "partner_ids": [(6, 0, record.partner_ids.ids)],
                    }
                )

                # Crear la caja
                box_wizard.create_packing_products()

            pallet_default_code = (
                record.name.default_code + record.sufix
                if record.name.default_code and record.sufix
                else None
            )
            if pallet_default_code:
                domain = [
                    ("default_code", "=", pallet_default_code),
                ]
            else:
                domain = [
                    ("name", "=", record.name.name + " - " + template.printed_code),
                    ("pnt_parent_id", "=", record.name.id),
                    ("pnt_parent_qty", "=", record.base_qty),
                    ("pnt_box_qty", "=", record.box_qty),
                ]
            exist = self.env["product.template"].search(domain)
            if not exist.ids:
                # PASO 2: Crear el PALLET usando el template original
                pallet_wizard = self.create(
                    {
                        "name": record.name.id,
                        "bom_template_id": record.bom_template_id.id,
                        "base_qty": record.base_qty,
                        "box_qty": record.box_qty,
                        "partner_ids": [(6, 0, record.partner_ids.ids)],
                    }
                )

                # Crear el pallet
                pallet_wizard.create_packing_products()

    def create_packing_products(self) -> None:
        """
        Crea productos de tipo empaquetado (caja o palet) a partir de un producto base.
        También crea la lista de materiales asociada y las entradas en las listas de
         precios
        de los clientes seleccionados.
        Asigna el empaquetado al producto base para vender por múltiplos.
        Si el empaquetado es de tipo caja, utiliza la plantilla de lista de materiales
        especificada en el campo bom_box_template_id.
        Si el empaquetado es de tipo palet, utiliza la plantilla de lista de materiales
        especificada en el campo bom_template_id.
        """
        for record in self:
            # Tipo de empaquetado PALET o Caja:
            # Cantidades base:

            sale_ok, purchase_ok = False, False
            type = record.bom_template_id.printed_code
            baseqty, boxqty = record.base_qty, record.box_qty
            packagetype = self.env.ref("product_inplast.package_type_box_inplast")

            # Chequeo de que todos los partner deseados tienen precio en su tarifa para
            # el producto base:
            pricelist_item = []
            for partner in record.partner_ids:
                base_pricelist_item = self.env["product.pricelist.item"].search(
                    [
                        ("pricelist_id", "=", partner.property_product_pricelist.id),
                        ("product_tmpl_id", "=", record.name.id),
                    ]
                )
                if base_pricelist_item.ids:
                    pricelist_item.append(base_pricelist_item)
                else:
                    message = "Missing base price in " + partner.name + " pricelist."
                    raise UserError(message)

            # Cambiar variables si no es tipo caja (será palet):
            if record.type not in ["box", "box_nonmrp"]:
                packagetype = self.env.ref(
                    "product_inplast.package_type_pallet_inplast"
                )
                sale_ok = True
                purchase_ok = True

            # Crear producto:
            code = ""
            # Comprobar si el producto ya existía:
            name = record.name.name + " - " + type
            exist = self.env["product.template"].search(
                [
                    ("name", "=", name),
                    ("pnt_parent_id", "=", record.name.id),
                    ("pnt_parent_qty", "=", record.base_qty),
                    ("pnt_box_qty", "=", record.box_qty),
                ]
            )
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
                    if record.type not in ["box", "box_nonmrp"]:
                        raise UserError(
                            'Código duplicado, cambia el último campo "Sufix".'
                        )
                    else:
                        raise UserError(
                            'Código duplicado, cambia el último campo "Sufix". en la '
                            "plantilla de caja."
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
                    "list_price": record.name.list_price * baseqty,
                    "ipnr_subject": ("yes" if record.name.ipnr_subject else "category"),
                    "categ_id": record.name.categ_id.id,
                    "standard_price": record.name.standard_price * baseqty,
                    "sale_ok": sale_ok,
                    "purchase_ok": purchase_ok,
                    "tracking": "lot",
                    "pnt_mrp_as_serial": True,
                    "route_ids": [(6, 0, [routemrp.id])],
                    "pnt_box_qty": boxqty,
                    "mrp_bom_template_id": record.bom_template_id.id,
                }
            )
            pwnr = record.name.plastic_weight_non_recyclable * baseqty
            newpacking.write(
                {
                    "ipnr_subject": record.name.ipnr_subject,
                    "tax_plastic_type": record.name.tax_plastic_type,
                    "plastic_weight_non_recyclable": pwnr,
                    "plastic_tax_weight": record.name.plastic_tax_weight * baseqty,
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
                # newbomboxline
                self.env["mrp.bom.line"].create(
                    {
                        "product_id": li.product_id.id,
                        "product_qty": li.quantity,
                        "bom_id": newldm.id,
                    }
                )

            # Incluir materiales desde la ldm de producto base, para palets y cajas
            # que fabricamos nosotros:
            if record.type in ["box", "pallet"]:
                if not record.name.bom_ids.ids:
                    raise UserError(
                        "Haz una lista de materiales con componentes o materiales "
                        "en el producto base "
                        "antes de crear empaquetados."
                    )
                else:
                    bom = record.name.bom_ids[0]
                    for li in bom.bom_line_ids:
                        # newbomline
                        self.env["mrp.bom.line"].create(
                            {
                                "product_id": li.product_id.id,
                                "pnt_raw_percent": li.pnt_raw_percent,
                                "product_qty": li.product_qty * baseqty,
                                "product_uom_id": li.product_uom_id.id,
                                "bom_id": newldm.id,
                            }
                        )
            # Para box_nonmrp y pallet_nonmrp no se añade línea base adicional. [TK124053]

            # Crear en cada tarifa de cliente la entrada del packing:
            for item in pricelist_item:
                # pricelistitem
                self.env["product.pricelist.item"].create(
                    {
                        "pricelist_id": item.pricelist_id.id,
                        "product_tmpl_id": newpacking.id,
                        "applied_on": "1_product",
                        "compute_price": "fixed",
                        "fixed_price": item.fixed_price * record.base_qty,
                    }
                )

            # Asignar packaging_ids (product.packaging) al nuevo producto del tipo
            # CAJA o PALET para huecos disponibles:
            product = self.env["product.product"].search(
                [("product_tmpl_id", "=", newpacking.id)]
            )[0]
            # newpackingtype
            self.env["product.packaging"].create(
                {
                    "name": record.type + " " + str(baseqty),
                    "package_type_id": packagetype.id,
                    "product_id": product.id,
                    "product_uom_id": product.uom_id.id,
                    "sales": True,
                    "purchase": True,
                    "qty": 1,
                    "mrp_bom_template_id": record.bom_template_id.id,
                }
            )

            self._recompute_created_packing_weight(newpacking)
            # Asignar packaging_ids (product.packaging) al producto base para
            # vender por múltiplos:
            product = self.env["product.product"].search(
                [("product_tmpl_id", "=", record.name.id)]
            )[0]

            # newpackingtype
            self.env["product.packaging"].create(
                {
                    "name": record.type + " " + str(baseqty),
                    "package_type_id": packagetype.id,
                    "product_id": product.id,
                    "product_uom_id": product.uom_id.id,
                    "sales": True,
                    "purchase": True,
                    "qty": baseqty,
                    "mrp_bom_template_id": record.bom_template_id.id,
                }
            )
