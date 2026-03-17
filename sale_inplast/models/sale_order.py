import logging
from datetime import datetime
from typing import Any

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    total_pallets = fields.Integer(
        "Total pallets",
        compute="_compute_total_pallets",
        store=True,
    )
    total_boxes = fields.Integer(
        "Total boxes",
        compute="_compute_total_boxes",
        store=True,
    )

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        if 'incoterm' in fields_list:
            partner_id = vals.get('partner_id')
            if partner_id:
                partner = self.env['res.partner'].browse(partner_id)
                if partner.default_incoterm_id:
                    vals['incoterm'] = partner.default_incoterm_id.id
        return vals

    @api.onchange('partner_id')
    def _onchange_partner_id_incoterm(self):
        if self.partner_id and self.partner_id.default_incoterm_id:
            self.incoterm = self.partner_id.default_incoterm_id

    def _auto_add_delivery_line(self) -> None:
        """Añade automáticamente la línea de delivery si no existe"""
        self.ensure_one()

        # Verificar si ya tiene línea de delivery o si no tiene líneas de pedido
        # Usar la misma condición que el botón de Odoo para mostrar "Add shipping"
        if self.delivery_set or not self.order_line or self.is_all_service:
            return

        # Obtener el carrier del partner o de la compañía
        carrier = (
            self.with_company(
                self.company_id
            ).partner_shipping_id.property_delivery_carrier_id
            or self.with_company(
                self.company_id
            ).partner_shipping_id.commercial_partner_id.property_delivery_carrier_id
            or self.company_id.pnt_exwork_delivery_mode_id
        )

        if not carrier:
            return

        # Calcular el precio del envío
        try:
            vals = carrier.with_context(
                order_weight=self._get_estimated_weight()
            ).rate_shipment(self)
            if vals.get("success"):
                delivery_price = vals.get("price", 0.0)
                delivery_message = vals.get("warning_message", False)

                # Crear la línea de delivery usando set_delivery_line
                # que internamente ya llama a _remove_delivery_line si existe
                self.set_delivery_line(carrier, delivery_price)

                # Actualizar campos adicionales sin usar write para evitar recursión
                delivery_vals = {"recompute_delivery_price": False}
                if delivery_message:
                    delivery_vals["delivery_message"] = delivery_message
                super().write(delivery_vals)
        except Exception as e:
            # Si hay error al calcular el precio, registrar pero no fallar
            _logger.warning(
                "Error al añadir automáticamente línea de delivery para SO %s: %s",
                self.name,
                str(e),
            )

    def write(self, vals: dict) -> bool:
        res = super().write(vals)
        # Ejecutar auto-add delivery solo si se modifican líneas de pedido
        # y no estamos en un contexto de skip_auto_delivery
        if "order_line" in vals and not self.env.context.get("skip_auto_delivery"):
            for order in self:
                order._auto_add_delivery_line()
        return res

    @api.depends("order_line", "order_line.active")
    def _compute_total_pallets(self):
        for order in self:
            total_pallets = 0
            for line in order.order_line.filtered("active"):
                if (
                    line.product_id.pnt_product_type == "packing"
                    and line.product_id.mrp_bom_template_id.type
                    in ("pallet", "pallet_nonmrp")
                ):
                    if line.product_uom_qty and line.product_uom_qty > 0:
                        total_pallets += line.product_uom_qty

            order.total_pallets = total_pallets

    @api.depends("order_line", "order_line.active")
    def _compute_total_boxes(self):
        for order in self:
            total_boxes = 0
            for line in order.order_line.filtered("active"):
                if (
                    line.product_id.pnt_product_type == "packing"
                    and line.product_id.mrp_bom_template_id.type
                    in ("box", "box_nonmrp")
                ):
                    if line.product_uom_qty and line.product_uom_qty > 0:
                        total_boxes += line.product_uom_qty

            order.total_boxes = total_boxes

    # Campos de estado de la tarifa:
    @api.depends("state", "order_line", "pricelist_id.pnt_state")
    def _get_sale_pricelist_state(self):
        for record in self:
            state = record.pnt_pricelist_state
            if (record.state in ["draft", "sent"]) and (
                record.invoice_status in ["no", "to_invoice"]
            ):
                state = record.pricelist_id.pnt_state
            record["pnt_pricelist_state"] = state

    pnt_pricelist_state = fields.Selection(
        [("active", "Active"), ("update", "Update"), ("locked", "Locked")],
        string="Pricelist state",
        store=True,
        copy=False,
        compute="_get_sale_pricelist_state",
    )

    pnt_last_price_update = fields.Datetime(
        "Last price update", default=lambda self: datetime.now()
    )

    @api.onchange("incoterm")
    def _onchange_incoterm_id(self) -> None:
        """
        Asigna automáticamente la ciudad en incoterm_location según el tipo de incoterm:
        - Si is_exwork = True: ciudad de la empresa
        - Si is_exwork = False o no definido: ciudad del cliente
        """
        if self.incoterm:
            self.incoterm_location = self._compute_incoterm_location()

    def _compute_incoterm_location(self) -> str | bool:
        """
        Calcula la ciudad a asignar en incoterm_location basado en el incoterm
        """
        if not self.incoterm:
            return False

        # Obtener el valor de is_exwork, por defecto False si no está definido
        is_exwork = getattr(self.incoterm, "is_exwork", False)

        if is_exwork:
            # Incoterm tipo Exwork: usar ciudad de la empresa
            if self.company_id and self.company_id.partner_id:
                return self.company_id.partner_id.city or False
        else:
            # Incoterm no Exwork: usar ciudad del cliente
            if self.partner_id:
                return self.partner_id.city or False

        return False

    def pnt_action_update_prices(self):
        for record in self:
            record.action_update_prices()
            record["pnt_last_price_update"] = datetime.now()

    @api.depends("order_line", "state")
    def _get_sale_update_prices_required(self):
        for record in self:
            required = False
            last_update = record.pricelist_id.pnt_last_update
            if (
                (record.invoice_status in ["no", "to_invoice"])
                and (last_update)
                and (record.pnt_last_price_update < last_update)
            ):
                required = True
            record["pnt_update_prices"] = required

    pnt_update_prices = fields.Boolean(
        "Update prices", store=False, compute="_get_sale_update_prices_required"
    )

    # Restricción para que no se puedan cambiar de estado los pedidos con tarifas
    # bloqueadas:
    @api.constrains("state")
    def _avoid_sales_with_locked_pricelist_and_final_products(self):
        for record in self:
            if record.pnt_pricelist_state == "locked":
                raise UserError(
                    "Pedido bloqueado, revisa y actualiza la tarifa del cliente: "
                    + record.partner_id.name
                )
            if (record.pnt_update_prices) and (
                record.state in ["sent", "draft", "sale"]
            ):
                raise UserError(
                    "Precios obsoletos, se requiere actualizar precios para: "
                    + record.partner_id.name
                )
            for li in record.order_line:
                if (li.product_id.pnt_product_type == "final") and (
                    record.state in ["sent", "sale"]
                ):
                    raise UserError(
                        "Pedido con producto final, cámbialo por uno tipo PACKING"
                        " (caja o palet)."
                    )

            else:
                return True

    # Cambiar las líneas de venta de tapones sueltos por CAJAS o PALETS, si tienen
    # packaging asignado:
    def update_order_lines_with_related_box_pallet_products(self):
        pricelist_products = self.pricelist_id.item_ids.product_tmpl_id  # noqa: F841
        for li in self.order_line:
            # Si el producto no tiene packaging asignado, no se puede cambiar por un
            # packaging:
            if (
                not li.product_packaging_id
                and li.product_id.pnt_product_type == "final"
            ):
                raise UserError(
                    "No se puede cambiar el producto por un packaging, ya que"
                    " no tiene packaging asignado: " + li.product_id.name
                )

            # Si el producto tiene packaging asignado, se busca el packaging
            # relacionado:
            if li.product_packaging_id.id:
                packaging = self.env["product.packaging"].search(
                    [
                        ("product_id", "=", li.product_id.id),
                        ("qty", "=", li.product_packaging_id.qty),
                        ("id", "in", li.customer_packaging_ids.ids),
                    ],
                    limit=1,
                )
                if packaging.id:
                    pppackaging = self.env["product.product"].search(
                        [
                            ("pnt_parent_id", "=", li.product_id.product_tmpl_id.id),
                            ("pnt_parent_qty", "=", li.product_packaging_id.qty),
                            (
                                "mrp_bom_template_id",
                                "=",
                                packaging.mrp_bom_template_id.id,
                            ),
                            ("pnt_product_type", "=", "packing"),
                        ],
                        limit=1,
                    )
                    mrppackaging = self.env["product.packaging"].search(
                        [("product_id", "=", pppackaging.id), ("qty", "=", 1)]
                    )
                    if pppackaging.id and mrppackaging.id and packaging:
                        if (
                            not li.product_uom_qty
                            or li.product_uom_qty < li.product_packaging_id.qty
                        ):
                            raise UserError(
                                f"La cantidad para el producto:"
                                f" {li.product_id.name}"
                                f" no puede ser inferior a"
                                f" {li.product_packaging_id.qty}"
                                f" que es la que indica el empaquetado:"
                                f" {li.product_packaging_id.name}"
                            )
                        price = (
                            li.price_unit
                            * li.product_uom_qty
                            / li.product_packaging_qty
                        )
                        qty = li.product_packaging_qty
                        li.write(
                            {
                                "product_id": pppackaging.id,
                                "product_uom_qty": qty,
                                "price_unit": price,
                                "product_packaging_id": mrppackaging.id,
                                "product_packaging_qty": qty,
                            }
                        )

    def _get_order_lines_to_report(self):
        """Override to filter out archived lines from reports."""
        lines = super()._get_order_lines_to_report()
        return lines.filtered(lambda line: line.active)

    def action_archive_selected_lines(
        self,
    ) -> dict[str, str | list[tuple[str, str, Any]] | dict[str, bool | Any] | Any]:
        """Open wizard to manage archive status of all order lines."""
        return {
            "type": "ir.actions.act_window",
            "name": "Manage Order Lines Archive Status",
            "res_model": "sale.order.line",
            "view_mode": "tree",
            "view_id": self.env.ref(
                "sale_inplast.sale_order_line_archive_wizard_tree"
            ).id,
            "domain": [("order_id", "=", self.id)],
            "context": {
                "default_order_id": self.id,
                "sale_order_archive_mode": True,
                "active_test": False,  # This ensures both active and inactive lines
                # are shown
            },
            "target": "new",
        }
