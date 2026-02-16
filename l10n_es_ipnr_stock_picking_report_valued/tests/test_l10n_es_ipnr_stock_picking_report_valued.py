# Copyright 2024 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.l10n_es_ipnr_account.tests.common import TestL10nEsInprCommon


class TestL10nEsInprStockPickingReportValued(TestL10nEsInprCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.tax = cls.env["account.tax"].create(
            {"name": "Tax 21.0%", "amount": 21.0, "amount_type": "percent"}
        )
        cls.env.ref("l10n_es_ipnr_account.aportacion_ipnr_product_template").write(
            {"taxes_id": [cls.tax.id]}
        )

    def test_valued_picking_ipnr_amount(self):
        sale = self.env["sale.order"].create(
            {
                "company_id": self.company.id,
                "partner_id": self.partner.id,
                "date_order": "2023-01-01",
                "fiscal_position_id": self.fiscal_position_ipnr.id,
                "order_line": [
                    (
                        0,
                        False,
                        {
                            "product_id": self.product_ipnr_in_product.id,
                            "product_uom_qty": 10,
                            "price_unit": 2,
                            "tax_id": [self.tax.id],
                        },
                    )
                ],
            }
        )
        sale.action_confirm()
        sale.write({"date_order": "2023-01-01"})
        picking = sale.picking_ids

        # No 'done' quantity
        line = picking.move_line_ids
        self.assertAlmostEqual(line.ipnr_amount_subtotal, 0.6, places=2)
        self.assertAlmostEqual(line.ipnr_amount_tax, 0.126, places=2)
        self.assertAlmostEqual(line.ipnr_amount_total, 0.726, places=2)
        self.assertAlmostEqual(picking.ipnr_amount_subtotal, 0.6, places=2)
        self.assertAlmostEqual(picking.ipnr_amount_tax, 0.126, places=2)
        self.assertAlmostEqual(picking.ipnr_amount_total, 0.726, places=2)
        self.assertAlmostEqual(
            picking.picking_total_with_ipnr, sale.amount_total, places=2
        )

        # With 'done' quantity
        line.write({"quantity": 6})
        # Force amounts recomputation, as stock_picking_report_valued module d
        # does not do it
        line._compute_sale_order_line_fields()
        picking._compute_amount_all()
        self.assertAlmostEqual(line.ipnr_amount_subtotal, 0.36, places=2)
        self.assertAlmostEqual(line.ipnr_amount_tax, 0.0756, places=2)
        self.assertAlmostEqual(line.ipnr_amount_total, 0.4356, places=2)
        self.assertAlmostEqual(picking.ipnr_amount_subtotal, 0.36, places=2)
        self.assertAlmostEqual(picking.ipnr_amount_tax, 0.0756, places=2)
        self.assertAlmostEqual(picking.ipnr_amount_total, 0.4356, places=2)
        self.assertAlmostEqual(picking.picking_total_with_ipnr, 14.9556, places=2)

        # All 'done'
        line.write({"quantity": 10})
        # Force amounts recomputation, as stock_picking_report_valued module d
        # does not do it
        line._compute_sale_order_line_fields()
        picking._compute_amount_all()
        self.assertAlmostEqual(line.ipnr_amount_subtotal, 0.6, places=2)
        self.assertAlmostEqual(line.ipnr_amount_tax, 0.126, places=2)
        self.assertAlmostEqual(line.ipnr_amount_total, 0.726, places=2)
        self.assertAlmostEqual(picking.ipnr_amount_subtotal, 0.6, places=2)
        self.assertAlmostEqual(picking.ipnr_amount_tax, 0.126, places=2)
        self.assertAlmostEqual(picking.ipnr_amount_total, 0.726, places=2)
        self.assertAlmostEqual(
            picking.picking_total_with_ipnr, sale.amount_total, places=2
        )
