from datetime import datetime
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = "account.move"

    def _pnt_recompute_price_unit_preserve_discount(
        self, lines: models.Model
    ) -> None:
        """Recompute price unit from pricelist while preserving manual discount."""
        if not lines:
            return
        discount_field = "discount"
        if lines._fields.get("discount1"):
            discount_field = "discount1"
        discount_map = {
            line.id: line[discount_field]
            for line in lines
            if line[discount_field]
        }
        lines._compute_price_unit()
        for line in lines:
            if line.id in discount_map:
                line.with_context(check_move_validity=False)[
                    discount_field
                ] = discount_map[line.id]

    def _pnt_check_pricelist_packing_products(self):
        """
        Validación previa a la actualización de precios:
        - Para cada línea de factura con producto tipo 'packing', toma su producto padre.
        - Busca en el padre sus 'pnt_packing_ids' cuyo 'mrp_bom_template_id' sea el del
          embalaje de la línea y, si aplica, también el 'box_template_id' de esa plantilla.
        - Comprueba que todos esos embalajes existen en la lista de precios de la factura.
        """
        PricelistItem = self.env["product.pricelist.item"]

        errors = []
        for move in self:
            if not move.invoice_line_ids:
                continue

            packing_lines = move.invoice_line_ids.filtered(
                lambda l: l.product_id and l.product_id.pnt_product_type == "packing"
            )
            if not packing_lines:
                continue

            if not move.pricelist_id:
                errors.append(
                    f"{move.display_name}: la factura no tiene lista de precios asignada."
                )
                continue

            required_packings = self.env["product.template"]
            missing_packings_in_parent = {}  # (parent_id, template_id) -> (parent, template)

            for line in packing_lines:
                packing_tmpl = line.product_id.product_tmpl_id
                parent = packing_tmpl.pnt_parent_id
                if not parent:
                    continue
                # También exigimos que el producto base (pnt_parent_id) esté en la tarifa.
                required_packings |= parent

                template = packing_tmpl.mrp_bom_template_id
                templates_to_check = self.env["product.bom.template"]
                if template:
                    templates_to_check |= template
                    if template.box_template_id:
                        templates_to_check |= template.box_template_id

                if not templates_to_check:
                    # Si el embalaje no tiene plantilla, al menos exigimos que el
                    # propio producto esté tarifado.
                    required_packings |= packing_tmpl
                    continue

                siblings = parent.pnt_packing_ids.filtered(
                    lambda p: p.active
                    and p.mrp_bom_template_id.id in templates_to_check.ids
                )
                required_packings |= siblings

                # Si falta alguno de los templates esperados en el padre, lo reportamos.
                found_template_ids = set(siblings.mapped("mrp_bom_template_id").ids)
                for tmpl in templates_to_check:
                    if tmpl.id not in found_template_ids:
                        missing_packings_in_parent[(parent.id, tmpl.id)] = (parent, tmpl)

            if missing_packings_in_parent:
                msg_lines = [
                    f"{move.display_name}: faltan embalajes configurados en el producto padre (pnt_packing_ids):"
                ]
                for parent, tmpl in missing_packings_in_parent.values():
                    msg_lines.append(f"- {parent.display_name}: plantilla {tmpl.name}")
                errors.append("\n".join(msg_lines))

            if not required_packings:
                continue

            required_packings = required_packings.filtered("active")
            if not required_packings:
                continue

            required_product_ids = required_packings.mapped("product_variant_ids").ids
            items = PricelistItem.search(
                [
                    ("pricelist_id", "=", move.pricelist_id.id),
                    "|",
                    ("product_tmpl_id", "in", required_packings.ids),
                    ("product_id", "in", required_product_ids),
                ]
            )
            present_template_ids = set(items.mapped("product_tmpl_id").ids)
            present_template_ids |= set(items.mapped("product_id.product_tmpl_id").ids)

            missing = required_packings.filtered(
                lambda p: p.id not in present_template_ids
            )
            if missing:
                msg_lines = [
                    f"{move.display_name}: faltan embalajes en la lista de precios de la factura "
                    f"({move.pricelist_id.display_name}):"
                ]
                for product in missing:
                    template = product.mrp_bom_template_id
                    template_info = (
                        f" (plantilla: {template.name})" if template else ""
                    )
                    msg_lines.append(f"- {product.display_name}{template_info}")
                msg_lines.append("Añádelos a la tarifa y vuelve a actualizar precios.")
                errors.append("\n".join(msg_lines))

        if errors:
            raise UserError("\n\n".join(errors))

    @api.depends("state", "invoice_line_ids", "pricelist_id.pnt_state")
    def _get_invoice_pricelist_state(self):
        for record in self:
            state = False
            if (record.move_type in ["out_invoice"]) and (record.state == "draft"):
                state = record.pricelist_id.pnt_state
                if record.state in ["draft", "sent"]:
                    state = record.pricelist_id.pnt_state
            record["pnt_pricelist_state"] = state

    pnt_pricelist_state = fields.Selection(
        [("active", "Active"), ("update", "Update"), ("locked", "Locked")],
        string="Pricelist state",
        store=True,
        copy=False,
        compute="_get_invoice_pricelist_state",
    )

    pnt_last_price_update = fields.Datetime(
        "Last price update", default=lambda self: datetime.now()
    )

    def action_post(self) -> bool:
        if self.move_type in ["out_invoice"]:
            self._pnt_check_pricelist_packing_products()
        lines_to_update = self.env["account.move.line"]
        for line in self.invoice_line_ids:
            has_pricelist = self.env["product.pricelist.item"].search(
                [
                    ("pricelist_id", "=", self.pricelist_id.id),
                    ("product_tmpl_id", "=", line.product_id.product_tmpl_id.id),
                ]
            )
            if len(has_pricelist) > 1:
                raise UserError("El producto tiene más de un precio en la lista de precios:" + line.product_tmpl_id.name)
            if has_pricelist and (has_pricelist.fixed_price != line.price_unit):
                lines_to_update |= line
        if lines_to_update:
            self._pnt_recompute_price_unit_preserve_discount(lines_to_update)
        # result = super(AccountMove, self).button_update_prices_from_pricelist()
        result = super(AccountMove, self).action_post()
        self.pnt_last_price_update = datetime.now()
        return result

    def button_update_prices_from_pricelist(self) -> bool:
        self._pnt_check_pricelist_packing_products()
        # Evitar tocar líneas IPNR: el módulo de IPNR puede borrar/regenerar
        # dichas líneas, provocando "Registro faltante" si se recalculan precios
        # sobre el recordset completo.
        moves = self.filtered(lambda r: r.state == "draft")
        lines = moves.invoice_line_ids
        if lines._fields.get("is_ipnr"):
            lines = lines.filtered(lambda l: not l.is_ipnr)
        if lines._fields.get("is_icc"):
            lines = lines.filtered(lambda l: not l.is_icc)
        self._pnt_recompute_price_unit_preserve_discount(lines)

        # Recalcular IPNR al final (si está instalado) para reflejar posibles cambios.
        if moves._fields.get("is_ipnr") and hasattr(moves, "apply_ipnr"):
            ipnr_moves = moves.filtered(
                lambda m: m.is_ipnr and m.ipnr_is_date and m.state == "draft"
            )
            if ipnr_moves and hasattr(ipnr_moves, "_delete_ipnr"):
                ipnr_moves.with_context(avoid_recursion=True)._delete_ipnr()
                ipnr_moves.apply_ipnr()

        # Recalcular ICC al final (si está instalado) por el mismo motivo.
        if moves._fields.get("is_icc") and hasattr(moves, "apply_icc"):
            icc_moves = moves.filtered(
                lambda m: m.is_icc and m.icc_is_date and m.state == "draft"
            )
            if icc_moves and hasattr(icc_moves, "_delete_icc"):
                icc_moves.with_context(avoid_recursion=True)._delete_icc()
                icc_moves.apply_icc()

        result = True
        self.pnt_last_price_update = datetime.now()
        return result

    @api.depends("invoice_line_ids", "state")
    def _get_invoice_update_prices_required(self):
        for record in self:
            required = False
            last_update = record.pricelist_id.pnt_last_update
            if (
                (record.state in ["draft"])
                and (last_update)
                and (record.pnt_last_price_update < last_update)
            ):
                required = True
            record["pnt_update_prices"] = required

    pnt_update_prices = fields.Boolean(
        "Update prices", store=False, compute="_get_invoice_update_prices_required"
    )
