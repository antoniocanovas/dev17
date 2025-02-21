# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestAnalyticDistribution(TransactionCase):
    def setUp(self):
        super(TestAnalyticDistribution, self).setUp()
        # ----------------------------------------------------------------------------
        # Creación de un partner para las órdenes de venta
        # ----------------------------------------------------------------------------
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})

        # ----------------------------------------------------------------------------
        # Obtenemos la unidad de medida "Unidad" (se utiliza en movimientos y líneas de venta)
        # ----------------------------------------------------------------------------
        self.uom_unit = self.env.ref('uom.product_uom_unit')

        # ----------------------------------------------------------------------------
        # Creación de las categorías con el campo 'type' correspondiente.
        # Estas categorías serán asignadas a los productos.
        # ----------------------------------------------------------------------------
        self.cat_handle = self.env['product.category'].create({
            'name': 'Handle Category',
            'type': 'handle',
        })
        self.cat_cap_mrp = self.env['product.category'].create({
            'name': 'Cap MRP Category',
            'type': 'cap_mrp',
        })
        self.cat_cap_distribution = self.env['product.category'].create({
            'name': 'Cap Distribution Category',
            'type': 'cap_distribution',
        })
        self.cat_raw_cistern = self.env['product.category'].create({
            'name': 'Raw Cistern Category',
            'type': 'raw_cistern',
        })
        self.cat_raw_sack = self.env['product.category'].create({
            'name': 'Raw Sack Category',
            'type': 'raw_sack',
        })
        self.cat_raw_color = self.env['product.category'].create({
            'name': 'Raw Color Category',
            'type': 'raw_color',
        })
        self.cat_raw_pallet = self.env['product.category'].create({
            'name': 'Raw Pallet Category',
            'type': 'raw_pallet',
        })
        self.cat_raw_cardboard = self.env['product.category'].create({
            'name': 'Raw Cardboard Category',
            'type': 'raw_cardboard',
        })
        self.cat_raw_bag = self.env['product.category'].create({
            'name': 'Raw Bags Category',
            'type': 'raw_bags',
        })
        self.cat_other = self.env['product.category'].create({
            'name': 'Other Category',
            'type': 'other',
        })

        # ----------------------------------------------------------------------------
        # Creación de productos asignando la categoría respectiva.
        # Cada producto tendrá asignada una categoría, y esta a su vez posee el type correcto.
        # ----------------------------------------------------------------------------
        self.product_handle = self.env['product.product'].create({
            'name': 'Product Handle',
            'categ_id': self.cat_handle.id,
        })
        self.product_cap_mrp = self.env['product.product'].create({
            'name': 'Product Cap MRP',
            'categ_id': self.cat_cap_mrp.id,
        })
        self.product_cap_distribution = self.env['product.product'].create({
            'name': 'Product Cap Distribution',
            'categ_id': self.cat_cap_distribution.id,
        })
        self.product_raw_cistern = self.env['product.product'].create({
            'name': 'Product Raw Cistern',
            'categ_id': self.cat_raw_cistern.id,
        })
        self.product_raw_sack = self.env['product.product'].create({
            'name': 'Product Raw Sack',
            'categ_id': self.cat_raw_sack.id,
        })
        self.product_raw_color = self.env['product.product'].create({
            'name': 'Product Raw Color',
            'categ_id': self.cat_raw_color.id,
        })
        self.product_raw_pallet = self.env['product.product'].create({
            'name': 'Product Raw Pallet',
            'categ_id': self.cat_raw_pallet.id,
        })
        self.product_raw_cardboard = self.env['product.product'].create({
            'name': 'Product Raw Cardboard',
            'categ_id': self.cat_raw_cardboard.id,
        })
        self.product_raw_bag = self.env['product.product'].create({
            'name': 'Product Raw Bag',
            'categ_id': self.cat_raw_bag.id,
        })

        # ----------------------------------------------------------------------------
        # Creación del registro de Analytic Distribution con las fechas de análisis.
        # Sólo se tendrán en cuenta los documentos (pickings y sale orders)
        # cuyas fechas estén entre date_from y date_to.
        # ----------------------------------------------------------------------------
        self.analytic_distribution = self.env['analytic.distribution'].create({
            'date_from': '2025-01-01',
            'date_to': '2025-01-31',
        })

    # ----------------------------------------------------------------------------
    # Métodos auxiliares para crear documentos (pickings y sale orders)
    # ----------------------------------------------------------------------------
    def create_stock_picking(self, scheduled_date, product, quantity):
        """Crea un albarán (stock.picking) y su movimiento asociado.
        Se asigna un producto (que a su vez ya tiene su categoría con type correcto)
        """
        picking = self.env['stock.picking'].create({
            'scheduled_date': scheduled_date,
            # Dependiendo de la versión, puede ser necesario definir el picking_type_id u otros campos.
        })
        self.env['stock.move'].create({
            'picking_id': picking.id,
            'product_id': product.id,
            'product_uom_qty': quantity,
            'product_uom': self.uom_unit.id,
            # Otros campos mínimos podrían ser requeridos.
        })
        return picking

    def create_sale_order(self, date_order, product, quantity):
        """Crea una orden de venta (sale.order) y su línea.
        Se asigna un producto que tiene la categoría con su type correspondiente.
        """
        sale_order = self.env['sale.order'].create({
            'date_order': date_order,
            'partner_id': self.partner.id,
        })
        self.env['sale.order.line'].create({
            'order_id': sale_order.id,
            'product_id': product.id,
            'product_uom_qty': quantity,
            'product_uom': self.uom_unit.id,
            # Otros campos mínimos podrían ser requeridos.
        })
        return sale_order

    # ----------------------------------------------------------------------------
    # Casos de prueba para verificar el comportamiento según la fecha y la categoría
    # ----------------------------------------------------------------------------
    def test_picking_in_handles(self):
        """Prueba que un albarán con producto de categoría 'handle' y fecha en rango
        se incluya en los cálculos del Analytic Distribution.
        """
        # Picking dentro del rango con producto 'handle' y cantidad 10
        picking_in_range = self.create_stock_picking('2025-01-15', self.product_handle, 10)
        self.analytic_distribution._compute_picking_in_handles_ids()
        self.analytic_distribution._compute_picking_in_handles_qty()
        self.analytic_distribution._compute_picking_in_handles()
        self.assertIn(picking_in_range, self.analytic_distribution.picking_in_handles_ids)
        self.assertEqual(self.analytic_distribution.picking_in_handles_qty, 1)
        self.assertEqual(self.analytic_distribution.picking_in_pallet_handles_qty, 10)

        # Picking fuera de rango (no debe incluirse)
        picking_out = self.create_stock_picking('2024-12-31', self.product_handle, 5)
        self.analytic_distribution._compute_picking_in_handles_ids()
        self.analytic_distribution._compute_picking_in_handles_qty()
        self.analytic_distribution._compute_picking_in_handles()
        self.assertNotIn(picking_out, self.analytic_distribution.picking_in_handles_ids)
        self.assertEqual(self.analytic_distribution.picking_in_pallet_handles_qty, 10)

    def test_picking_in_caps(self):
        """Prueba los albaranes con productos de categoría 'cap_mrp' y 'cap_distribution'."""
        picking1 = self.create_stock_picking('2025-01-10', self.product_cap_mrp, 20)
        picking2 = self.create_stock_picking('2025-01-20', self.product_cap_distribution, 30)
        self.analytic_distribution._compute_picking_in_caps_ids()
        self.analytic_distribution._compute_picking_in_caps_qty()
        self.analytic_distribution._compute_picking_in_caps()
        self.assertIn(picking1, self.analytic_distribution.picking_in_caps_ids)
        self.assertIn(picking2, self.analytic_distribution.picking_in_caps_ids)
        self.assertEqual(self.analytic_distribution.picking_in_caps_qty, 2)
        self.assertEqual(self.analytic_distribution.picking_in_pallet_caps_qty, 50)

        # Picking fuera de rango (no se debe incluir)
        picking_out = self.create_stock_picking('2025-02-01', self.product_cap_distribution, 15)
        self.analytic_distribution._compute_picking_in_caps_ids()
        self.analytic_distribution._compute_picking_in_caps_qty()
        self.analytic_distribution._compute_picking_in_caps()
        self.assertNotIn(picking_out, self.analytic_distribution.picking_in_caps_ids)
        self.assertEqual(self.analytic_distribution.picking_in_pallet_caps_qty, 50)

    def test_sale_order_caps(self):
        """Prueba las órdenes de venta con productos de categoría 'cap_mrp' y 'cap_distribution'."""
        so1 = self.create_sale_order('2025-01-10', self.product_cap_mrp, 20)
        so2 = self.create_sale_order('2025-01-20', self.product_cap_distribution, 30)
        self.analytic_distribution._compute_sale_caps_order_ids()
        self.analytic_distribution._compute_sale_caps_order_count()
        self.analytic_distribution._compute_sale_caps_order_qty()
        self.assertIn(so1, self.analytic_distribution.sale_caps_order_ids)
        self.assertIn(so2, self.analytic_distribution.sale_caps_order_ids)
        self.assertEqual(self.analytic_distribution.sale_caps_order_count, 2)
        self.assertEqual(self.analytic_distribution.sale_caps_order_qty, 50)

        # Sale order fuera de rango (no se debe incluir)
        so_out = self.create_sale_order('2025-02-01', self.product_cap_mrp, 10)
        self.analytic_distribution._compute_sale_caps_order_ids()
        self.analytic_distribution._compute_sale_caps_order_count()
        self.analytic_distribution._compute_sale_caps_order_qty()
        self.assertNotIn(so_out, self.analytic_distribution.sale_caps_order_ids)
        self.assertEqual(self.analytic_distribution.sale_caps_order_qty, 50)

    def test_sale_order_handles(self):
        """Prueba las órdenes de venta con productos de categoría 'handle'."""
        so = self.create_sale_order('2025-01-15', self.product_handle, 10)
        self.analytic_distribution._compute_sale_handles_order_ids()
        self.analytic_distribution._compute_sale_handles_order_count()
        self.analytic_distribution._compute_sale_handles_order_qty()
        self.assertIn(so, self.analytic_distribution.sale_handles_order_ids)
        self.assertEqual(self.analytic_distribution.sale_handles_order_count, 1)
        self.assertEqual(self.analytic_distribution.sale_handles_order_qty, 10)

        # Sale order fuera de rango
        so_out = self.create_sale_order('2024-12-31', self.product_handle, 5)
        self.analytic_distribution._compute_sale_handles_order_ids()
        self.analytic_distribution._compute_sale_handles_order_count()
        self.analytic_distribution._compute_sale_handles_order_qty()
        self.assertNotIn(so_out, self.analytic_distribution.sale_handles_order_ids)
        self.assertEqual(self.analytic_distribution.sale_handles_order_qty, 10)

    def test_picking_in_cistern(self):
        """Prueba los albaranes con productos de categoría 'raw_cistern'."""
        picking_in_range = self.create_stock_picking('2025-01-05', self.product_raw_cistern, 10)
        self.analytic_distribution._compute_picking_in_cistern_ids()
        self.analytic_distribution._compute_picking_in_cistern_qty()
        self.assertIn(picking_in_range, self.analytic_distribution.picking_in_cistern_ids)
        self.assertEqual(self.analytic_distribution.picking_in_cistern_qty, 1)

        picking_out = self.create_stock_picking('2024-12-31', self.product_raw_cistern, 10)
        self.analytic_distribution._compute_picking_in_cistern_ids()
        self.analytic_distribution._compute_picking_in_cistern_qty()
        self.assertNotIn(picking_out, self.analytic_distribution.picking_in_cistern_ids)

    def test_picking_in_sack(self):
        """Prueba los albaranes con productos de categoría 'raw_sack'."""
        picking = self.create_stock_picking('2025-01-15', self.product_raw_sack, 25)
        self.analytic_distribution._compute_picking_in_sack_ids()
        self.analytic_distribution._compute_picking_in_sack_qty()
        self.assertIn(picking, self.analytic_distribution.picking_in_sack_ids)
        self.assertEqual(self.analytic_distribution.picking_in_sack_qty, 1)

    def test_picking_in_color(self):
        """Prueba los albaranes con productos de categoría 'raw_color'."""
        picking = self.create_stock_picking('2025-01-28', self.product_raw_color, 5)
        self.analytic_distribution._compute_picking_in_color_ids()
        self.analytic_distribution._compute_picking_in_color_qty()
        self.assertIn(picking, self.analytic_distribution.picking_in_color_ids)
        self.assertEqual(self.analytic_distribution.picking_in_color_qty, 1)

    def test_picking_in_cardboard(self):
        """Prueba los albaranes con productos de categoría 'raw_cardboard'."""
        picking = self.create_stock_picking('2025-01-18', self.product_raw_cardboard, 12)
        self.analytic_distribution._compute_picking_in_cardboard_ids()
        self.analytic_distribution._compute_picking_in_cardboard_qty()
        self.assertIn(picking, self.analytic_distribution.picking_in_cardboard_ids)
        self.assertEqual(self.analytic_distribution.picking_in_cardboard_qty, 1)

    def test_picking_in_bag(self):
        """Prueba los albaranes con productos de categoría 'raw_bag'."""
        picking = self.create_stock_picking('2025-01-29', self.product_raw_bag, 40)
        self.analytic_distribution._compute_picking_in_bag_ids()
        self.analytic_distribution._compute_picking_in_bag_qty()
        self.assertIn(picking, self.analytic_distribution.picking_in_bag_ids)
        self.assertEqual(self.analytic_distribution.picking_in_bag_qty, 1)
