# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestL10nEsIpnrCommon(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("base.main_company")
        cls.company.write({"ipnr_enable": True, "ipnr_date_from": "2022-01-01"})
        cls.partner = cls.env["res.partner"].create({"name": "Test"})
        cls.fiscal_position_ipnr = cls.env["account.fiscal.position"].create(
            {"name": "Test Fiscal Ipnr", "active": True, "ipnr_subject": True}
        )
        cls.fiscal_position_no_ipnr = cls.env["account.fiscal.position"].create(
            {"name": "Test Fiscal Ipnr", "active": True, "ipnr_subject": False}
        )
        cls.category_ipnr = cls.env["product.category"].create(
            {"name": "Ipnr Category", "ipnr_subject": True}
        )
        cls.product_ipnr_no = cls.env["product.product"].create(
            {
                "name": "Product-1",
                "ipnr_subject": "no",
                "weight": 1,
            }
        )
        cls.product_ipnr_in_product = cls.env["product.product"].create(
            {
                "name": "Product (IPNR in product)",
                "ipnr_subject": "yes",
                "weight": 1,
            }
        )
        cls.product_ipnr_in_category = cls.env["product.product"].create(
            {
                "name": "Product (IPNR in category)",
                "ipnr_subject": "category",
                "weight": 2,
                "categ_id": cls.category_ipnr.id,
            }
        )
        cls.product_ipnr_in_category_excluded = cls.env["product.product"].create(
            {
                "name": "Product (IPNR in category excluded)",
                "ipnr_subject": "no",
                "weight": 3,
                "categ_id": cls.category_ipnr.id,
            }
        )
        cls.product_ipnr_no_weight = cls.env["product.product"].create(
            {
                "name": "Product (IPNR no weight)",
                "ipnr_subject": "yes",
                "weight": 0,
            }
        )
