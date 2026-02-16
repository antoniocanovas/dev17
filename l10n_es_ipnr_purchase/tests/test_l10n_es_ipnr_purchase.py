# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError

from odoo.addons.l10n_es_ipnr_account.tests.common import TestL10nEsIpnrCommon


class TestL10nEsIpnrPurchase(TestL10nEsIpnrCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_ipnr_no.write(
            {
                "purchase_method": "purchase",
            }
        )
        cls.product_ipnr_in_product.write(
            {
                "purchase_method": "purchase",
            }
        )
        cls.product_ipnr_in_category.write(
            {
                "purchase_method": "purchase",
            }
        )
        cls.product_ipnr_in_category_excluded.write(
            {
                "purchase_method": "purchase",
            }
        )
        cls.product_ipnr_no_weight.write(
            {
                "purchase_method": "purchase",
            }
        )

    def create_purchase_order(self, date, fiscal_position, lines, ipnr_no=False):
        order_lines = []
        for line in lines:
            order_lines.append(
                (
                    0,
                    False,
                    {
                        "product_id": line["product"].id,
                        "product_qty": line["quantity"],
                        "price_unit": line["price_unit"],
                    },
                )
            )
        vals = {
            "company_id": self.company.id,
            "partner_id": self.partner.id,
            "date_order": date,
            "fiscal_position_id": fiscal_position.id,
            "order_line": order_lines,
        }
        if ipnr_no:
            vals["is_ipnr"] = False
        return self.env["purchase.order"].create(vals)

    def test_purchase_without_ipnr_products(self):
        lines = [{"product": self.product_ipnr_no, "quantity": 2.0, "price_unit": 1}]
        purchase = self.create_purchase_order(
            "2023-01-01", self.fiscal_position_ipnr, lines
        )
        self.assertEqual(purchase.ipnr_company, True)
        self.assertEqual(purchase.ipnr_has_line, False)
        self.assertEqual(purchase.amount_untaxed, 2)

    def test_purchase_with_ipnr_products_no_weight(self):
        lines = [
            {"product": self.product_ipnr_no_weight, "quantity": 2.0, "price_unit": 1}
        ]
        purchase = self.create_purchase_order(
            "2023-01-01", self.fiscal_position_ipnr, lines
        )
        self.assertTrue(purchase.ipnr_automated_exception_id)

    def test_purchase_with_ipnr(self):
        lines = [
            {
                "product": self.product_ipnr_in_product,
                "quantity": 1.0,
                "price_unit": 2,
            },
            {
                "product": self.product_ipnr_in_category,
                "quantity": 2.0,
                "price_unit": 3,
            },
            {
                "product": self.product_ipnr_in_category_excluded,
                "quantity": 3.0,
                "price_unit": 4,
            },
        ]
        purchase = self.create_purchase_order(
            "2023-01-01", self.fiscal_position_ipnr, lines, True
        )
        self.assertEqual(purchase.ipnr_has_line, False)
        self.assertEqual(purchase.amount_untaxed, 20.00)
        product_ipnr_in_product_line = purchase.order_line.filtered(
            lambda a: a.product_id == self.product_ipnr_in_product
        )
        self.assertEqual(product_ipnr_in_product_line.ipnr_amount, 0.06)
        product_ipnr_in_category_line = purchase.order_line.filtered(
            lambda a: a.product_id == self.product_ipnr_in_category
        )
        self.assertEqual(product_ipnr_in_category_line.ipnr_amount, 0.24)
        product_ipnr_in_category_excluded_line = purchase.order_line.filtered(
            lambda a: a.product_id == self.product_ipnr_in_category_excluded
        )
        self.assertEqual(product_ipnr_in_category_excluded_line.ipnr_amount, 0.00)

        purchase.write({"is_ipnr": True})
        self.assertEqual(purchase.ipnr_has_line, True)
        self.assertEqual(purchase.amount_untaxed, 20.3)
        purchase.write(
            {
                "order_line": [
                    (
                        0,
                        False,
                        {
                            "product_id": self.product_ipnr_in_product.id,
                            "product_qty": 1.0,
                            "price_unit": 2,
                        },
                    )
                ]
            }
        )
        self.assertEqual(purchase.amount_untaxed, 22.36)
        purchase.write({"is_ipnr": False})
        self.assertEqual(purchase.amount_untaxed, 22.00)

    def test_single_invoice_from_purchase(self):
        lines = [
            {
                "product": self.product_ipnr_in_product,
                "quantity": 1.0,
                "price_unit": 2,
            },
            {
                "product": self.product_ipnr_in_category,
                "quantity": 2.0,
                "price_unit": 3,
            },
            {
                "product": self.product_ipnr_in_category_excluded,
                "quantity": 3.0,
                "price_unit": 4,
            },
        ]
        purchase = self.create_purchase_order(
            "2023-01-01", self.fiscal_position_ipnr, lines
        )
        purchase.button_confirm()
        purchase.action_create_invoice()
        invoice = purchase.invoice_ids[0]
        self.assertEqual(invoice.ipnr_has_line, True)
        self.assertEqual(invoice.amount_untaxed, 20.3)

        # Delete SIGAUS line from invoice a recreate it.
        # It needs to be related to the SIGAUS line in the sale order.
        invoice.invoice_line_ids.filtered(lambda a: a.is_ipnr).unlink()
        ipnr_line_in_order = purchase.order_line.filtered(lambda a: a.is_ipnr)
        ipnr_line_in_invoice = invoice.invoice_line_ids.filtered(
            lambda a: a.is_ipnr
        )
        self.assertEqual(ipnr_line_in_order, ipnr_line_in_invoice.purchase_line_id)

        invoice_copy = invoice.copy()
        self.assertTrue(invoice_copy.is_ipnr)
        self.assertTrue(invoice_copy.ipnr_has_line)
        ipnr_line_in_copy_order = invoice_copy.invoice_line_ids.filtered("is_ipnr")
        self.assertEqual(len(ipnr_line_in_copy_order), 1)
        self.assertEqual(
            ipnr_line_in_copy_order.purchase_line_id, ipnr_line_in_order
        )
        invoice_copy.write(
            {
                "invoice_line_ids": [
                    (
                        0,
                        False,
                        {
                            "product_id": self.product_ipnr_in_product.id,
                            "quantity": 1.0,
                            "price_unit": 2,
                        },
                    )
                ]
            }
        )

        copy_invoice_ipnr_lines = invoice_copy.invoice_line_ids.filtered("is_ipnr")
        self.assertEqual(len(copy_invoice_ipnr_lines), 2)
        ipnr_line_in_copy_order_from_purchase = copy_invoice_ipnr_lines.filtered(
            "purchase_line_id"
        )
        self.assertEqual(len(ipnr_line_in_copy_order_from_purchase), 1)
        self.assertEqual(
            ipnr_line_in_copy_order_from_purchase.purchase_line_id,
            ipnr_line_in_order,
        )
        independent_ipnr_line_in_copy_order = copy_invoice_ipnr_lines.filtered(
            lambda a: not a.purchase_line_id
        )
        self.assertEqual(len(independent_ipnr_line_in_copy_order), 1)

    def test_invoice_from_multiple_purchases(self):
        lines_1 = [
            {
                "product": self.product_ipnr_in_product,
                "quantity": 1.0,
                "price_unit": 2,
            }
        ]
        purchase_1 = self.create_purchase_order(
            "2023-01-01", self.fiscal_position_ipnr, lines_1
        )
        lines_2 = [
            {
                "product": self.product_ipnr_in_category,
                "quantity": 2.0,
                "price_unit": 3,
            }
        ]
        purchase_2 = self.create_purchase_order(
            "2023-01-01", self.fiscal_position_ipnr, lines_2
        )
        purchase_1_ipnr_line = purchase_1.order_line.filtered(lambda a: a.is_ipnr)
        purchase_1.button_confirm()
        purchase_2_ipnr_line = purchase_2.order_line.filtered(lambda a: a.is_ipnr)
        purchase_2.button_confirm()
        (purchase_1 + purchase_2).action_create_invoice()
        invoice = purchase_1.invoice_ids[0]
        ipnr_lines = invoice.invoice_line_ids.filtered(lambda a: a.is_ipnr)
        self.assertEqual(len(ipnr_lines), 2)
        invoice_purchase_1_ipnr_line = invoice.invoice_line_ids.filtered(
            lambda a: a.purchase_line_id == purchase_1_ipnr_line
        )
        self.assertTrue(invoice_purchase_1_ipnr_line)
        invoice_purchase_2_ipnr_line = invoice.invoice_line_ids.filtered(
            lambda a: a.purchase_line_id == purchase_2_ipnr_line
        )
        self.assertTrue(invoice_purchase_2_ipnr_line)

        # Delete and regenerate one of the SIGAUS lines in invoice
        invoice_purchase_1_ipnr_line.unlink()
        ipnr_lines = invoice.invoice_line_ids.filtered(lambda a: a.is_ipnr)
        self.assertEqual(len(ipnr_lines), 2)
        invoice_purchase_1_ipnr_line = invoice.invoice_line_ids.filtered(
            lambda a: a.purchase_line_id == purchase_1_ipnr_line
        )
        self.assertTrue(
            invoice_purchase_1_ipnr_line.price_subtotal,
            purchase_1_ipnr_line.price_subtotal,
        )
        self.assertTrue(invoice_purchase_1_ipnr_line)
        invoice_purchase_2_ipnr_line = invoice.invoice_line_ids.filtered(
            lambda a: a.purchase_line_id == purchase_2_ipnr_line
        )
        self.assertTrue(
            invoice_purchase_2_ipnr_line.price_subtotal,
            purchase_2_ipnr_line.price_subtotal,
        )
        self.assertTrue(invoice_purchase_2_ipnr_line)

        invoice_copy = invoice.copy()
        self.assertTrue(invoice_copy.is_ipnr)
        self.assertTrue(invoice_copy.ipnr_has_line)
        self.assertEqual(len(invoice_copy.invoice_line_ids.filtered("is_ipnr")), 2)
        invoice_copy.write(
            {
                "invoice_line_ids": [
                    (
                        0,
                        False,
                        {
                            "product_id": self.product_ipnr_in_product.id,
                            "quantity": 1.0,
                            "price_unit": 2,
                        },
                    )
                ]
            }
        )
        copy_invoice_ipnr_lines = invoice_copy.invoice_line_ids.filtered("is_ipnr")
        self.assertEqual(len(copy_invoice_ipnr_lines), 3)
        ipnr_lines_in_copy_order_from_purchase = copy_invoice_ipnr_lines.filtered(
            "purchase_line_id"
        )
        self.assertEqual(len(ipnr_lines_in_copy_order_from_purchase), 2)
        self.assertTrue(
            ipnr_lines_in_copy_order_from_purchase.filtered(
                lambda a: a.purchase_line_id == purchase_1_ipnr_line
            )
        )
        self.assertTrue(
            ipnr_lines_in_copy_order_from_purchase.filtered(
                lambda a: a.purchase_line_id == purchase_2_ipnr_line
            )
        )
        independent_ipnr_line_in_copy_order = copy_invoice_ipnr_lines.filtered(
            lambda a: not a.purchase_line_id
        )
        self.assertEqual(len(independent_ipnr_line_in_copy_order), 1)

    def test_ipnr_purchase_copy(self):
        lines = [
            {
                "product": self.product_ipnr_in_product,
                "quantity": 1.0,
                "price_unit": 2,
            },
            {
                "product": self.product_ipnr_in_category,
                "quantity": 2.0,
                "price_unit": 3,
            },
            {
                "product": self.product_ipnr_in_category_excluded,
                "quantity": 3.0,
                "price_unit": 4,
            },
        ]
        purchase = self.create_purchase_order(
            "2023-01-01", self.fiscal_position_ipnr, lines
        )
        purchase_copy = purchase.copy({"date_order": purchase.date_order})
        self.assertEqual(purchase.amount_untaxed, purchase_copy.amount_untaxed)
        self.assertTrue(purchase_copy.is_ipnr)
        self.assertTrue(purchase_copy.ipnr_has_line)
        self.assertEqual(len(purchase_copy.order_line.filtered("is_ipnr")), 1)
        self.assertEqual(
            purchase_copy.order_line.filtered("is_ipnr").price_subtotal, 0.3
        )

    def test_cancel_purchase(self):
        lines = [
            {
                "product": self.product_ipnr_in_product,
                "quantity": 1.0,
                "price_unit": 2,
            },
            {
                "product": self.product_ipnr_in_category,
                "quantity": 2.0,
                "price_unit": 3,
            },
            {
                "product": self.product_ipnr_in_category_excluded,
                "quantity": 3.0,
                "price_unit": 4,
            },
        ]
        purchase = self.create_purchase_order(
            "2023-01-01", self.fiscal_position_ipnr, lines
        )
        purchase.button_confirm()
        purchase.action_create_invoice()
        ipnr_line = purchase.order_line.filtered(lambda a: a.is_ipnr)
        ipnr_invoice_line = ipnr_line.invoice_lines
        self.assertTrue(ipnr_invoice_line)
        purchase.button_cancel()
        self.assertEqual(purchase.state, "cancel")
        purchase.button_draft()
        self.assertEqual(purchase.state, "draft")
        ipnr_line = purchase.order_line.filtered(lambda a: a.is_ipnr)
        self.assertEqual(ipnr_line.invoice_lines, ipnr_invoice_line)

    def test_purchase_error_date(self):
        lines = [
            {
                "product": self.product_ipnr_in_product,
                "quantity": 1.0,
                "price_unit": 2,
            }
        ]
        with self.assertRaises(ValidationError):
            self.create_purchase_order("2022-01-01", self.fiscal_position_ipnr, lines)

    def test_add_ipnr_line_create_method(self):
        purchase = self.create_purchase_order(
            "2023-01-01", self.fiscal_position_ipnr, []
        )
        self.env["purchase.order.line"].create(
            {
                "product_id": self.product_ipnr_in_category_excluded.id,
                "product_qty": 1.0,
                "price_unit": 2,
                "order_id": purchase.id,
            }
        )
        self.assertEqual(purchase.ipnr_company, True)
        self.assertEqual(purchase.ipnr_has_line, False)
        self.assertEqual(purchase.amount_untaxed, 2)
        self.env["purchase.order.line"].create(
            {
                "product_id": self.product_ipnr_in_product.id,
                "product_qty": 3.0,
                "price_unit": 3,
                "order_id": purchase.id,
            }
        )
        self.assertEqual(purchase.ipnr_company, True)
        self.assertEqual(purchase.ipnr_has_line, True)
        self.assertEqual(purchase.amount_untaxed, 11.18)
        purchase.order_line.filtered(
            lambda a: a.product_id == self.product_ipnr_in_product
        ).write(
            {
                "product_qty": 6.0,
            }
        )
        self.assertEqual(purchase.ipnr_company, True)
        self.assertEqual(purchase.ipnr_has_line, True)
        self.assertEqual(purchase.amount_untaxed, 20.36)
        purchase.write(
            {
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_ipnr_in_category.id,
                            "product_uom_qty": 2,
                            "price_unit": 1,
                            "product_qty": 2.0,
                        },
                    ),
                ],
            }
        )
        self.assertEqual(purchase.ipnr_company, True)
        self.assertEqual(purchase.ipnr_has_line, True)
        self.assertEqual(purchase.amount_untaxed, 22.6)
