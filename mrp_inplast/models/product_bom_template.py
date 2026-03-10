from typing import Any

from odoo import _, fields, models


class ProductBomTemplate(models.Model):
    _name = "product.bom.template"
    _description = "Product bom template"

    name = fields.Char("Name")
    code = fields.Char("Sufix code")
    printed_code = fields.Char("Printed code")
    type = fields.Selection(
        [
            ("box", "Box"),
            ("pallet", "Pallet"),
            ("box_nonmrp", "Box third parties"),
            ("pallet_nonmrp", "Pallet third parties"),
        ],
        string="Packing type",
    )

    box_template_id = fields.Many2one(
        "product.bom.template", domain="[('type','in',['box','box_nonmrp'])]"
    )

    line_ids = fields.One2many(
        "product.bom.template.line", "template_id", string="Lines", copy=True
    )

    def action_apply_template_components(
        self,
    ) -> dict[str, str | dict[str, bool | str | Any]]:
        """Sync template components into every linked BoM."""
        total_boms = 0
        for template in self:
            boms = self.env["mrp.bom"].search(
                [("product_tmpl_id.mrp_bom_template_id", "=", template.id)]
            )
            if not boms:
                continue
            for bom in boms:
                commands = [(5, 0, 0)]
                for sequence, line in enumerate(template.line_ids, start=1):
                    line_vals = {
                        "product_id": line.product_id.id,
                        "product_qty": line.quantity,
                        "sequence": sequence * 10,
                    }
                    if line.product_id.uom_id:
                        line_vals["product_uom_id"] = line.product_id.uom_id.id
                    if bom.company_id:
                        line_vals["company_id"] = bom.company_id.id
                    commands.append((0, 0, line_vals))
                bom.write({"bom_line_ids": commands})
            total_boms += len(boms)

        if not total_boms:
            message = _(
                "No se encontraron LdM vinculadas a las plantillas seleccionadas."
            )
            message_type = "warning"
        else:
            message = _(
                "Se actualizaron %(boms)s LdM con los componentes"
                " de las plantillas seleccionadas."
            ) % {"boms": total_boms}
            message_type = "info"

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Plantillas de LdM"),
                "message": message,
                "sticky": False,
                "type": message_type,
            },
        }
