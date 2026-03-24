from odoo import api, models


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    @api.model
    def read_group(
        self,
        domain: list,
        fields: list,
        groupby: list,
        offset: int = 0,
        limit: int | None = None,
        orderby: str | bool = False,
        lazy: bool = True,
    ) -> list[dict]:
        """Override read_group for pivot/graph views"""
        if self.env.context.get("filter_exclude_ipnr_product"):
            # Obtener el ID del producto IPNR dinámicamente
            ipnr_product = self.env.ref(
                "l10n_es_ipnr_account.aportacion_ipnr_product_template",
                raise_if_not_found=False,
            )
            if ipnr_product:
                ipnr_domain = [("product_id", "!=", ipnr_product.id)]
                domain = domain + ipnr_domain

        return super().read_group(domain, fields, groupby, offset, limit, orderby, lazy)
