# -*- coding: utf-8 -*-
from odoo import models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_open_unbuild_wizard(self):
        """
        This action redirects to the product.product action.
        It is designed to be called from the product.template form view.
        """
        self.ensure_one()
        # The wizard will be opened for the first variant, but the wizard itself
        # allows selecting a lot/serial, which implicitly selects the variant.
        # The context passes the default product_id to help the wizard.
        return self.product_variant_id.action_open_unbuild_wizard()
