import logging
from typing import Any

from odoo import api, fields, models

from odoo.addons.base.models.res_partner import Partner as BaseResPartner
from odoo.addons.sale.models.res_partner import ResPartner as SaleResPartner

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    # Parche caliente
    SaleResPartner._commercial_fields = BaseResPartner._commercial_fields
    SaleResPartner._company_dependent_commercial_fields = (
        BaseResPartner._company_dependent_commercial_fields
    )

    property_product_pricelist = fields.Many2one(
        "product.pricelist",
        store=True,
        index=True,
        string="Pricelist",
        help="Esta lista de precios es específica para este partner.",
    )
    pnt_pricelist_state = fields.Selection(
        related="property_product_pricelist.pnt_state",
        store=True,
        string="Pricelist State",
    )
    pnt_next_update = fields.Date(
        related="property_product_pricelist.pnt_next_update", string="Next Update"
    )
    default_incoterm_id = fields.Many2one(
        "account.incoterms",
        string="Default Incoterm",
    )

    @api.model
    def create(self, vals: dict[str, Any]) -> "ResPartner":
        """
        Crea el partner y, opcionalmente, su pricelist privada.
        """
        partner = super().create(vals)
        # partner.create_private_pricelist()
        return partner

    def create_private_pricelist(self) -> None:
        for partner in self:
            _logger.info("Creando lista de precios privada para %s", partner.name)
            pricelist = self.env["product.pricelist"].create(
                {
                    "name": partner.name,
                }
            )
            partner.property_product_pricelist = pricelist
