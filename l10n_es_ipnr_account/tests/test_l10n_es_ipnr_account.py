# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError

from .common import TestL10nEsIpnrCommon


class TestL10nEsIpnrInvoice(TestL10nEsIpnrCommon):
    def create_invoice(self, date, lines, ipnr_no=False):
        invoice_lines = []
        for line in lines:
            invoice_lines.append(
                (
                    0,
                    False,
                    {
                        "product_id": line["product"].id,
                        "quantity": line["quantity"],
                        "price_unit": line["price_unit"],
                    },
                )
            )
        invoice = self.env["account.move"].create(
            {
                "company_id": self.company.id,
                "partner_id": self.partner.id,
                "invoice_date": date,
                "invoice_line_ids": invoice_lines,
                "move_type": "out_invoice",
                "is_ipnr": not ipnr_no,
            }
        )
        return invoice

    def create_reversal(self, reversal_type):
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
        invoice = self.create_invoice("2023-01-01", lines)
        invoice.action_post()
        move_reversal = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=[invoice.id])
            .create(
                {
                    "date": "2023-01-01",
                    "refund_method": reversal_type,
                    "journal_id": invoice.journal_id.id,
                }
            )
        )
        return invoice, move_reversal.reverse_moves()

    def test_invoice_without_ipnr_products(self):
        lines = [{"product": self.product_ipnr_no, "quantity": 2.0, "price_unit": 1}]
        invoice = self.create_invoice("2023-01-01", lines)
        self.assertEqual(invoice.ipnr_has_line, False)
        self.assertEqual(invoice.amount_untaxed, 2)

    def test_invoice_with_ipnr_products_no_weight(self):
        lines = [
            {"product": self.product_ipnr_no_weight, "quantity": 2.0, "price_unit": 1}
        ]
        invoice = self.create_invoice("2023-01-01", lines)
        self.assertEqual(invoice.ipnr_company, True)
        self.assertTrue(invoice.ipnr_automated_exception_id)

    def test_invoice_with_ipnr(self):
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
        invoice = self.create_invoice("2023-01-01", lines, True)
        self.assertEqual(invoice.ipnr_has_line, False)
        self.assertEqual(invoice.amount_untaxed, 20.00)
        product_ipnr_in_product_line = invoice.invoice_line_ids.filtered(
            lambda a: a.product_id == self.product_ipnr_in_product
        )
        self.assertEqual(product_ipnr_in_product_line.ipnr_amount, 0.06)
        product_ipnr_in_category_line = invoice.invoice_line_ids.filtered(
            lambda a: a.product_id == self.product_ipnr_in_category
        )
        self.assertEqual(product_ipnr_in_category_line.ipnr_amount, 0.24)
        product_ipnr_in_product_line = invoice.invoice_line_ids.filtered(
            lambda a: a.product_id == self.product_ipnr_in_product
        )
        self.assertEqual(product_ipnr_in_product_line.ipnr_amount, 0.06)
        product_ipnr_in_category_excluded_line = invoice.invoice_line_ids.filtered(
            lambda a: a.product_id == self.product_ipnr_in_category_excluded
        )
        self.assertEqual(product_ipnr_in_category_excluded_line.ipnr_amount, 0.00)

        invoice.write({"is_ipnr": True})
        self.assertEqual(invoice.ipnr_has_line, True)
        self.assertEqual(invoice.amount_untaxed, 20.3)
        invoice.write(
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
        self.assertEqual(invoice.amount_untaxed, 22.36)
        invoice.write({"fiscal_position_id": self.fiscal_position_no_ipnr.id})
        self.assertEqual(invoice.amount_untaxed, 22.00)
        invoice.write({"fiscal_position_id": False})
        self.assertEqual(invoice.amount_untaxed, 22.36)
        invoice.write({"is_ipnr": False})
        self.assertEqual(invoice.amount_untaxed, 22.00)

    def test_invoice_with_ipnr_general_reverse(self):
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
        invoice = self.create_invoice("2023-01-01", lines)
        invoice_ipnr_line = invoice.invoice_line_ids.filtered("is_ipnr")
        invoice.action_post()
        credit_note = invoice._reverse_moves()
        credit_note.write({"invoice_date": invoice.invoice_date})
        self.assertEqual(credit_note.move_type, "out_refund")
        self.assertEqual(invoice.amount_untaxed, credit_note.amount_untaxed)
        self.assertTrue(credit_note.is_ipnr)
        credit_note_ipnr_line = credit_note.invoice_line_ids.filtered("is_ipnr")
        self.assertEqual(len(credit_note_ipnr_line), 1)
        self.assertEqual(
            invoice_ipnr_line.price_subtotal, credit_note_ipnr_line.price_subtotal
        )

    def test_invoice_with_ipnr_reverse_refund(self):
        invoice, reversal = self.create_reversal("refund")
        invoice_ipnr_line = invoice.invoice_line_ids.filtered("is_ipnr")
        credit_note = self.env["account.move"].browse(reversal["res_id"])
        self.assertEqual(credit_note.move_type, "out_refund")
        self.assertEqual(invoice.amount_untaxed, credit_note.amount_untaxed)
        self.assertTrue(credit_note.is_ipnr)
        credit_note_ipnr_line = credit_note.invoice_line_ids.filtered("is_ipnr")
        self.assertEqual(len(credit_note_ipnr_line), 1)
        self.assertEqual(
            invoice_ipnr_line.price_subtotal, credit_note_ipnr_line.price_subtotal
        )
        self.assertEqual(
            invoice_ipnr_line.amount_currency,
            -1 * credit_note_ipnr_line.amount_currency,
        )

    def test_invoice_with_ipnr_reverse_cancel(self):
        invoice, reversal = self.create_reversal("cancel")
        invoice_ipnr_line = invoice.invoice_line_ids.filtered("is_ipnr")
        self.assertEqual(invoice.payment_state, "reversed")
        credit_note = self.env["account.move"].browse(reversal["res_id"])
        self.assertEqual(credit_note.move_type, "out_refund")
        self.assertEqual(invoice.amount_untaxed, credit_note.amount_untaxed)
        self.assertTrue(credit_note.is_ipnr)
        credit_note_ipnr_line = credit_note.invoice_line_ids.filtered("is_ipnr")
        self.assertEqual(len(credit_note_ipnr_line), 1)
        self.assertEqual(
            invoice_ipnr_line.price_subtotal, credit_note_ipnr_line.price_subtotal
        )
        self.assertEqual(
            invoice_ipnr_line.amount_currency,
            -1 * credit_note_ipnr_line.amount_currency,
        )

    def test_invoice_with_ipnr_reverse_modify(self):
        invoice, reversal = self.create_reversal("modify")
        invoice_ipnr_line = invoice.invoice_line_ids.filtered("is_ipnr")
        self.assertEqual(invoice.payment_state, "reversed")
        new_invoice = self.env["account.move"].browse(reversal["res_id"])
        new_invoice.write({"invoice_date": invoice.invoice_date})
        self.assertEqual(new_invoice.move_type, "out_invoice")
        self.assertEqual(invoice.amount_untaxed, new_invoice.amount_untaxed)
        self.assertTrue(new_invoice.is_ipnr)
        new_invoice_ipnr_line = new_invoice.invoice_line_ids.filtered("is_ipnr")
        self.assertEqual(len(new_invoice_ipnr_line), 1)
        self.assertEqual(
            invoice_ipnr_line.price_subtotal, new_invoice_ipnr_line.price_subtotal
        )
        self.assertEqual(
            invoice_ipnr_line.amount_currency, new_invoice_ipnr_line.amount_currency
        )

    def test_invoice_with_ipnr_different_dates(self):
        self.company.write({"ipnr_date_from": "3000-01-01"})
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
        invoice = self.create_invoice(False, lines)
        self.assertFalse(invoice.ipnr_is_date)
        self.assertFalse(invoice.ipnr_has_line)
        invoice.write({"invoice_date": "3000-01-01"})
        self.assertTrue(invoice.ipnr_is_date)
        self.assertTrue(invoice.ipnr_has_line)
        self.company.write({"ipnr_date_from": "2023-01-01"})
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
        invoice = self.create_invoice(False, lines)
        self.assertTrue(invoice.ipnr_is_date)
        self.assertTrue(invoice.ipnr_has_line)

    def test_copy_ipnr_invoice(self):
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
        invoice = self.create_invoice("2023-01-01", lines)
        invoice_copy = invoice.copy({"invoice_date": "2023-01-01"})
        self.assertEqual(invoice.amount_untaxed, invoice_copy.amount_untaxed)
        self.assertTrue(invoice_copy.is_ipnr)
        self.assertTrue(invoice_copy.ipnr_has_line)
        self.assertEqual(len(invoice_copy.invoice_line_ids.filtered("is_ipnr")), 1)
        self.assertEqual(
            invoice_copy.invoice_line_ids.filtered("is_ipnr").price_subtotal, 0.3
        )
        invoice.write(
            {
                "invoice_line_ids": [
                    (
                        0,
                        False,
                        {
                            "product_id": self.product_ipnr_in_category.id,
                            "quantity": 2.0,
                            "price_unit": 3,
                        },
                    ),
                ]
            }
        )
        self.assertEqual(len(invoice_copy.invoice_line_ids.filtered("is_ipnr")), 1)
        self.assertEqual(
            invoice_copy.invoice_line_ids.filtered("is_ipnr").price_subtotal, 0.3
        )

    def test_invoice_error_date(self):
        lines = [
            {
                "product": self.product_ipnr_in_product,
                "quantity": 1.0,
                "price_unit": 2,
            }
        ]
        with self.assertRaises(ValidationError):
            self.create_invoice("2022-01-01", lines)
