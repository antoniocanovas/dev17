# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _compute_customer_lead(self):
        super(SaleOrderLine, self)._compute_customer_lead()
        self.order_id._get_logistic_days()
