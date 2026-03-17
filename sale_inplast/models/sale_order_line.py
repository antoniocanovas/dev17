import logging
from typing import Any

from markupsafe import Markup

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    active = fields.Boolean(
        default=True,
        help="By unchecking the active field, you may archive this order line"
        " without deleting it. "
        "Archived lines will not appear in printed reports.",
        tracking=True,
    )

    # Productos disponibles para este cliente, según su tarifa:
    pnt_product_ids = fields.Many2many(
        "product.product",
        store=False,
        string="Pricelist products",
        related="order_id.pricelist_id.pnt_product_ids",
    )

    pnt_product_type = fields.Selection(related="product_id.pnt_product_type")

    total_pallets = fields.Integer(
        "Pallets",
        compute="_compute_total_pallets",
        store=True,
        help="Total pallets in the order line",
    )
    total_boxes = fields.Integer(
        "Boxes",
        compute="_compute_total_boxes",
        store=True,
        help="Total boxes in the order line",
    )
    total_cap = fields.Integer(
        "Total Units",
        compute="_compute_total_cap_units",
        store=True,
        help="Total caps or hands in the order line",
    )

    total_bump = fields.Integer(
        "bump",
        compute="_compute_total_bump",
        store=True,
        help="Total bump in the order line",
    )

    @api.depends("total_pallets", "total_boxes")
    def _compute_total_bump(self):
        for line in self:
            if line.product_id.pnt_product_type == "packing":
                pallets = line.total_pallets if line.total_pallets else 0
                boxes = line.total_boxes if line.total_boxes else 0
                line.total_bump = pallets + boxes
            else:
                line.total_bump = 0

    @api.depends("product_uom_qty")
    def _compute_total_cap_units(self):
        for line in self:
            if line.product_id.pnt_product_type == "packing":
                line.total_cap = line.product_uom_qty * line.product_id.pnt_parent_qty

    @api.depends("product_uom_qty")
    def _compute_total_boxes(self):
        for line in self:
            if (
                line.product_id.pnt_product_type == "packing"
                and line.product_id.mrp_bom_template_id.type == "box"
            ):
                line.total_boxes = line.product_uom_qty
            else:
                line.total_boxes = 0

    @api.depends("product_uom_qty")
    def _compute_total_pallets(self):
        for line in self:
            if (
                line.product_id.pnt_product_type == "packing"
                and line.product_id.mrp_bom_template_id.type == "pallet"
            ):
                line.total_pallets = line.product_uom_qty
            else:
                line.total_pallets = 0

    @api.onchange(
        "product_uom_qty", "product_id", "product_packaging_id", "product_packaging_qty"
    )
    def _get_base_units(self):
        for li in self:
            qty = 0
            if (li.product_id.pnt_product_type == "packing") and (
                li.product_id.pnt_parent_qty > 0
            ):
                qty = li.product_uom_qty * li.product_id.pnt_parent_qty
            if li.product_id.pnt_product_type == "final":
                qty = li.product_uom_qty
            li["pnt_base_qty"] = qty

    pnt_base_qty = fields.Integer("Base qty", store=False, compute="_get_base_units")

    @api.onchange("product_uom_qty")
    def _get_packing_units_from_sale_qty(self):
        for li in self:
            base_qty = 0
            if li.product_id.pnt_product_type == "packing":
                base_qty = li.product_uom_qty * li.product_id.pnt_parent_qty
            li["pnt_base_sale_unit"] = base_qty

    pnt_base_sale_unit = fields.Integer(
        "Base", store=False, compute="_get_packing_units_from_sale_qty"
    )

    @api.onchange("list_price", "discount")
    def _get_1k_price(self):
        for record in self:
            price = record.price_unit * 1000
            if record.pnt_base_qty != 0:
                price = record.price_subtotal / record.pnt_base_qty * 1000
            record["pnt_base_1k_price"] = price

    pnt_base_1k_price = fields.Float("1K", compute="_get_1k_price")

    # Fecha manual para que el comercial indique la comprometida de llegada a casa del
    # cliente:
    customer_arrival_date = fields.Date(
        "Customer date", help="Customer committed date", store=True, tracking=True
    )
    effective_date = fields.Date(
        "Effective date",
        help="Date when the order line was delivered",
        store=True,
        compute="_compute_effective_date",
    )

    @api.depends("order_id.effective_date")
    def _compute_effective_date(self):
        for line in self:
            if line.move_ids:
                # Get the latest effective date from related stock moves
                effective_dates = line.order_id.mapped("effective_date")
                line.effective_date = max(effective_dates) if effective_dates else False
            else:
                line.effective_date = False

    # Campo para referencia antigua mientras se mantiene el
    # sistema de producción anterior
    # a Odoo, borrar después:
    old_default_code = fields.Char("Ref antigua")

    customer_packaging_ids = fields.Many2many(
        "product.packaging",
        store=False,
        string="Customer packaging",
        compute="_get_customer_packaging_ids",
    )

    @api.depends("order_id.pricelist_id", "order_id.partner_id", "product_id")
    def _get_customer_packaging_ids(self):
        for record in self:
            packaging_dom = []
            # Instead of looping through order_line, we're working with the current line
            pi = self.env["product.pricelist.item"].search(
                [
                    ("pricelist_id", "=", record.order_id.pricelist_id.id),
                    (
                        "product_tmpl_id.pnt_parent_id",
                        "=",
                        record.product_id.product_tmpl_id.id,
                    ),
                ]
            )
            bom_template = pi.product_tmpl_id.packaging_ids.mrp_bom_template_id

            for packaging_base in record.product_id.packaging_ids:
                if packaging_base.mrp_bom_template_id.id in bom_template.ids:
                    packaging_dom.append(packaging_base.id)

            record.customer_packaging_ids = [(6, 0, packaging_dom)]

    @api.depends(
        "product_id", "product_uom_qty", "product_uom", "customer_packaging_ids"
    )
    def _compute_product_packaging_id(self):
        super()._compute_product_packaging_id()
        for line in self:
            if line.customer_packaging_ids:
                suggested_packaging = (
                    line.customer_packaging_ids._find_suitable_product_packaging(
                        line.product_uom_qty, line.product_uom
                    )
                )
                if suggested_packaging:
                    line.product_packaging_id = suggested_packaging

    def toggle_active(self) -> None:
        """Toggle the active state of the order line."""
        for line in self:
            old_active = line.active  # noqa: F841
            line.active = not line.active

            # The tracking system will handle this automatically due to
            # tracking=True on active field

    @api.depends("qty_delivered", "product_uom_qty")
    def _compute_is_underdelivered(self):
        """Compute if delivered quantity is less than ordered quantity."""
        for line in self:
            line.is_underdelivered = (
                line.product_uom_qty > 0 and line.qty_delivered < line.product_uom_qty
            )

    is_underdelivered = fields.Boolean(
        "Under-delivered",
        compute="_compute_is_underdelivered",
        store=True,
        help="True when delivered quantity is less than ordered quantity",
    )
    qty_undelivered = fields.Float(
        "Undelivered Quantity",
        compute="_compute_qty_undelivered",
        store=True,
        help="Cantidad pendiente de servir",
    )

    @api.depends("product_uom_qty", "qty_delivered")
    def _compute_qty_undelivered(self):
        """Compute the undelivered quantity."""
        for line in self:
            line.qty_undelivered = max(0, line.product_uom_qty - line.qty_delivered)

    # Fields to track for changes
    _tracked_fields = [
        "product_id",
        "product_uom_qty",
        "price_unit",
        "discount",
        "product_uom",
        "name",
        "product_packaging_id",
        "product_packaging_qty",
        "active",
        "customer_arrival_date",
    ]

    def _get_field_display_value(self, field_name: str, value: Any) -> str:
        """Get display value for field tracking."""
        field = self._fields.get(field_name)
        if not field:
            return str(value) if value else ""

        if field.type == "many2one":
            if value:
                record = self.env[field.comodel_name].browse(value)
                return record.display_name if record.exists() else str(value)
            return ""
        elif field.type == "selection":
            if value:
                selection_dict = dict(field.selection)
                return selection_dict.get(value, str(value))
            return ""
        elif field.type == "boolean":
            return "Sí" if value else "No"
        elif field.type in ["float", "monetary"]:
            return f"{value:.2f}" if value else "0.00"
        elif field.type == "integer":
            return str(value) if value is not None else "0"
        else:
            return str(value) if value else ""

    def _get_field_label(self, field_name: str) -> str:
        """Get human-readable label for field."""
        # Custom labels for specific fields in Spanish
        labels = {
            "product_uom_qty": "Cantidad",
            "price_unit": "Precio unitario",
            "discount": "Descuento",
            "product_id": "Producto",
            "product_uom": "Unidad de medida",
            "customer_arrival_date": "Fecha llegada cliente",
            "product_packaging_id": "Empaquetado",
            "product_packaging_qty": "Cantidad empaquetado",
            "name": "Descripción",
            "active": "Activo",
        }

        if field_name in labels:
            return labels[field_name]

        # Fallback to field string or formatted field name
        field = self._fields.get(field_name)
        if field and field.string:
            return field.string

        return field_name.replace("_", " ").title()

    def write(self, vals: dict[str, Any]) -> bool:
        """Override write to track field changes and post to chatter."""
        # Store original values before update
        original_values: dict[int, dict[str, Any]] = {}
        for line in self:
            # Track changes in all states (removed draft exclusion)
            original_values[line.id] = {}
            for field_name in self._tracked_fields:
                if field_name in vals:
                    value = getattr(line, field_name)
                    # Store IDs for Many2one fields to avoid psycopg2 adaptation issues
                    field = line._fields.get(field_name)
                    if field and field.type == "many2one":
                        original_values[line.id][field_name] = (
                            value.id if hasattr(value, "id") else value
                        )
                    else:
                        original_values[line.id][field_name] = value

        result = super().write(vals)

        # Post changes to chatter
        for line in self:
            if line.id in original_values:  # Removed draft state exclusion
                changes: list[str] = []
                for field_name in self._tracked_fields:
                    if field_name in vals:
                        old_value = original_values[line.id][field_name]
                        new_value = getattr(line, field_name)

                        # Convert new Many2one objects to IDs for comparison
                        field = line._fields.get(field_name)
                        if field and field.type == "many2one":
                            new_value_compare = (
                                new_value.id if hasattr(new_value, "id") else new_value
                            )
                        else:
                            new_value_compare = new_value

                        if old_value != new_value_compare:
                            old_display = self._get_field_display_value(
                                field_name, old_value
                            )
                            new_display = self._get_field_display_value(
                                field_name, new_value_compare
                            )
                            field_label = self._get_field_label(field_name)

                            if field_name == "active" and not new_value:
                                # Special handling for archiving
                                changes.append("<li>Línea archivada</li>")
                            elif field_name == "active" and new_value and not old_value:
                                # Special handling for unarchiving
                                changes.append("<li>Línea desarchivada</li>")
                            else:
                                changes.append(
                                    f"<li>{field_label}: {old_display} → "
                                    f"{new_display}</li>"
                                )

                if changes:
                    product_name = (
                        line.product_id.name or line.name or "Línea sin producto"
                    )
                    message = Markup(
                        f"""<p><strong>Cambios en línea de pedido:</strong> """
                        f"""{product_name}</p>
<ul>{"".join(changes)}</ul>"""
                    )
                    line.order_id.message_post(
                        body=message,
                        message_type="notification",
                        subtype_xmlid="mail.mt_note",
                    )

        return result

    def unlink(self) -> Any:
        """Track line deletion in parent order chatter."""
        lines_to_track: list[tuple[Any, str, list[str]]] = []
        for line in self:
            # Track deletion in all states (removed draft exclusion)
            product_name = line.product_id.name or line.name or "Línea sin producto"

            # Gather important field values before deletion
            line_details: list[str] = []
            important_fields = [
                ("product_uom_qty", "Cantidad"),
                ("price_unit", "Precio unitario"),
                ("discount", "Descuento"),
                ("product_uom", "Unidad de medida"),
                ("product_packaging_qty", "Cantidad empaquetado"),
                ("customer_arrival_date", "Fecha llegada cliente"),
            ]

            for field_name, field_label in important_fields:
                value = getattr(line, field_name, None)
                if value:
                    # For Many2one fields, get the ID, for others use the value directly
                    field = line._fields.get(field_name)
                    if field and field.type == "many2one":
                        value_for_display = value.id if hasattr(value, "id") else value
                    else:
                        value_for_display = value

                    display_value = self._get_field_display_value(
                        field_name, value_for_display
                    )
                    line_details.append(f"<li>{field_label}: {display_value}</li>")

            lines_to_track.append((line.order_id, product_name, line_details))

        result = super().unlink()

        # Post deletion messages to parent orders
        for order, product_name, line_details in lines_to_track:
            details_html = (
                "".join(line_details)
                if line_details
                else "<li>Sin detalles adicionales</li>"
            )
            message = Markup(
                f"""<p><strong>Línea eliminada:</strong> {product_name}</p>
<ul>{details_html}</ul>"""
            )
            order.message_post(
                body=message, message_type="notification", subtype_xmlid="mail.mt_note"
            )

        return result
