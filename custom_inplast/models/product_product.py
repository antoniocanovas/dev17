from typing import Any

from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    # ========== CUSTOMER INFO COMMERCIAL PARTNER ENHANCEMENTS ==========

    def _get_commercial_partner_id(self, partner_id: int | bool | Any) -> int | bool:
        """
        Helper method to get the commercial partner ID from a given partner ID.
        This ensures we always search by the commercial partner (parent company)
        instead of individual contacts.
        """
        if not partner_id:
            return partner_id

        if isinstance(partner_id, models.BaseModel):
            return partner_id.commercial_partner_id.id

        partner = self.env["res.partner"].browse(partner_id)
        return partner.commercial_partner_id.id

    @api.model
    def _name_search(
        self,
        name: str,
        domain: list | None = None,
        operator: str = "ilike",
        limit: int | None = None,
        order: str | None = None,
    ) -> list[int]:
        """
        Override to search customerinfo using commercial partner ID.
        This allows child contacts to find products by their parent company's
        customer codes and names.
        """
        res = super()._name_search(
            name, domain=domain, operator=operator, limit=limit, order=order
        )

        res_ids = list(res)
        res_ids_len = len(res_ids)
        if not limit or res_ids_len >= limit:
            limit = (limit - res_ids_len) if limit else False
        if (
            not name
            and limit
            or not self._context.get("partner_id")
            or res_ids_len >= limit
        ):
            return res_ids
        limit -= res_ids_len

        # Get commercial partner ID for the search
        context_partner_id = self._context.get("partner_id")
        commercial_partner_id = self._get_commercial_partner_id(context_partner_id)

        customerinfo_ids = self.env["product.customerinfo"]._search(
            [
                ("partner_id", "=", commercial_partner_id),
                "|",
                ("product_code", operator, name),
                ("product_name", operator, name),
            ],
            limit=limit,
        )
        if not customerinfo_ids:
            return res_ids
        res_templates = self.browse(res_ids).mapped("product_tmpl_id")
        product_tmpls = (
            self.env["product.customerinfo"]
            .browse(customerinfo_ids)
            .mapped("product_tmpl_id")
            - res_templates
        )
        product_ids = list(
            self._search(
                [("product_tmpl_id", "in", product_tmpls.ids)],
                limit=limit,
            )
        )
        res_ids.extend(product_ids)
        return res_ids

    def _get_price_from_customerinfo(self, partner_id: int | bool) -> float:
        """
        Override to get customer price using commercial partner ID.
        This allows child contacts to get prices defined for their parent company.
        """
        self.ensure_one()
        if not partner_id:
            return 0.0

        # Only proceed if product_supplierinfo_for_customer is installed
        if not hasattr(self.env, "product.customerinfo"):
            has_super_method = hasattr(super(), "_get_price_from_customerinfo")
            return (
                super()._get_price_from_customerinfo(partner_id)
                if has_super_method
                else 0.0
            )

        # Get commercial partner for price lookup
        commercial_partner_id = self._get_commercial_partner_id(partner_id)
        partner = self.env["res.partner"].browse(commercial_partner_id)
        customerinfo = self._select_customerinfo(partner=partner)
        if customerinfo:
            return customerinfo.price
        return 0.0

    def _prepare_domain_customerinfo(self, params: dict) -> list:
        """
        Override to prepare domain using commercial partner ID.
        """
        self.ensure_one()
        partner_id = params.get("partner_id")

        # Use commercial partner ID for domain construction
        commercial_partner_id = self._get_commercial_partner_id(partner_id)

        return [
            ("partner_id", "=", commercial_partner_id),
            "|",
            ("product_id", "=", self.id),
            "&",
            ("product_tmpl_id", "=", self.product_tmpl_id.id),
            ("product_id", "=", False),
        ]

    def _select_customerinfo(
        self,
        partner: Any | bool = False,
        _quantity: float = 0.0,
        _date: Any | None = None,
        _uom_id: int | bool = False,
        params: dict | bool = False,
    ) -> Any:
        """
        Override to select customerinfo using commercial partner ID.
        Customer version of the standard `_select_seller`.
        """
        # Only proceed if product_supplierinfo_for_customer is installed
        if not hasattr(self.env, "product.customerinfo"):
            has_super_method = hasattr(super(), "_select_customerinfo")
            return (
                super()._select_customerinfo(partner, _quantity, _date, _uom_id, params)
                if has_super_method
                else self.env["product.customerinfo"]
            )

        if not params:
            params = dict()

        # Use commercial partner ID for customerinfo selection
        commercial_partner = partner.commercial_partner_id if partner else False
        partner_id = commercial_partner.id if commercial_partner else False
        params.update({"partner_id": partner_id})

        domain = self._prepare_domain_customerinfo(params)
        res = (
            self.env["product.customerinfo"]
            .search(domain)
            .sorted(lambda s: (s.sequence, s.min_qty, s.price, s.id))
        )
        res_1 = res.sorted("product_tmpl_id")[:1]
        return res_1
