# -*- coding: utf-8 -*-
# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from docutils.nodes import container
from odoo import fields, models, api
from odoo.exceptions import UserError


class AnalyticDistribution(models.Model):
    _inherit = 'analytic.distribution'

    def compute_distribution(self):
        """Extend this function with custom Inplast analytic compute modes"""
        super().compute_distribution()
        if not self.env.company.analytic_product_plan_id.id:
            raise UserError('Assign product plan before computing (Settings => Company)')

        # Borrar las línes de otros cálculos anteriores:
        self.env["account.analytic.line"].search(
            [("analytic_distribution_id", "=", self.id)]
        ).unlink()
        # Actualizar los parámetros generales analíticos de 'Analytic parameters' para este mes:
        self._update_general_parameters()

        # Calcular por líneas en función de cada plantilla:
        for li in self.line_ids:
            if li.template_id.compute_method == "demo":
                a = 1
                # raise UserError("ok")
            elif li.template_id.compute_method == "r1":
                self.compute_r1(li)
            elif li.template_id.compute_method == "r13":
                self.compute_r13(li)
            elif li.template_id.compute_method in ["r14", "r15"]:
                self.compute_r14(li)
            elif li.template_id.compute_method == "r22":
                self.compute_r22(li)

    def compute_r1(self, li):
        datefrom = self.date_from
        dateto = self.date_to
        picking_hour_cost = li.picking_hour_cost

        for picking in self.picking_in_handles_ids:
            products = set()
            total_pallets = 0

            # Total palets en albarán:
            lines = picking.move_ids_without_package.filtered(lambda l: l.product_id.categ_id.type == 'handle')
            total_pallets += sum(lines.mapped('product_uom_qty'))
            pallet_picking_unload = self.picking_unload / total_pallets

            # Productos distintos en el albarán, del tipo asa:
            for sm in lines:
                products.add(sm.product_id)
            # Bucle para cada apunte analítico:
            for product in products:
                product_pallets = 0
                for sm in lines:
                    if sm.product_id == product:
                        product_pallets += sm.product_uom_qty

                # Buscamos si ya existe o se crea la cuenta analítica para este producto:
                analytic_account = self.check_or_create_analytic_account(product)
                # Pdte: Ver si hay planes adicionales que cumplimentar, y cambiar el estándar account_id:
                if product_pallets > 0:
                    product_field_id = self.env.company.product_field_id.name
                    fixed_variable_field_id = self.env.company.fixed_variable_field_id.name
                    machine_field_id = self.env.company.machine_field_id.name
                    department_field_id = self.env.company.department_field_id.name

                    new_aal = self.env['account.analytic.line'].create({
                        'product_id': product.id,
                        'name': li.template_id.name,
                        'amount': - product_pallets * pallet_picking_unload * li.picking_hour_cost,
                        product_field_id: analytic_account.id,
                        'analytic_distribution_id': self.id,
                        'analytic_distribution_template_id': li.template_id.id,
                    })

    # =========================================================================
    # Traemos todos los campos de parámetros en el momento del recálculo y guardamos:
    # =========================================================================
    # Warehouse (load/unload)
    truck_load = fields.Float(
        string='Truck load',
        help="Time required to load a truck."
    )
    container_load = fields.Float(
        string='Container load',
        help="Time required to load a container."
    )
    picking_unload = fields.Float(
        string='Picking unload',
        help="Time required to unload per picking."
    )

    # Raw material reception (load/unload)
    raw_cistern_unload = fields.Float(
        string='Cistern unload',
        help="Time required to unload a cistern."
    )
    raw_sack_unload = fields.Float(
        string='Sack unload',
        help="Time required to unload sacks of raw material."
    )
    raw_color_unload = fields.Float(
        string='Color unload',
        help="Time required to unload color material."
    )
    raw_pallet_unload = fields.Float(
        string='Pallet unload',
        help="Time required to unload pallets."
    )
    raw_cardboard_unload = fields.Float(
        string='Cardboard unload',
        help="Time required to unload cardboard."
    )
    raw_bag_unload = fields.Float(
        string='Bag unload ',
        help="Time required to unload bags."
    )
    # Internal transfer to production
    raw_color_reloc_daily = fields.Float(
        string='Color',
        help="Daily internal relocation time for color (hours per day)."
    )
    raw_pallet_reloc_daily = fields.Float(
        string='Pallet ',
        help="Daily internal relocation time for pallets (hours per day)."
    )
    raw_cboard_reloc_daily = fields.Float(
        string='Cardboard',
        help="Daily internal relocation time for cardboard (hours per day)."
    )
    raw_bag_reloc_daily = fields.Float(
        string='Bag',
        help="Daily internal relocation time for bags (hours per day)."
    )
    # Other fields
    pallet_reloc = fields.Float(
        string='Minutes per pallet',
        help="Minutes required to relocate each pallet."
    )
    container_box_qty = fields.Integer(
        string='Boxes per container',
        help="Number of boxes that fit in a container."
    )

    def _update_general_parameters(self):
        parameters = self.env.ref('analytic_distribution_inplast.analytic_distribution_inplast_parameter')
        self.write({
            'truck_load': parameters.truck_load,
            'container_load': parameters.container_load,
            'picking_unload': parameters.picking_unload,
            'raw_cistern_unload': parameters.raw_cistern_unload,
            'raw_sack_unload': parameters.raw_sack_unload,
            'raw_color_unload': parameters.raw_color_unload,
            'raw_pallet_unload': parameters.raw_pallet_unload,
            'raw_cardboard_unload': parameters.raw_cardboard_unload,
            'raw_bag_unload': parameters.raw_bag_unload,
            'raw_color_reloc_daily': parameters.raw_color_reloc_daily,
            'raw_pallet_reloc_daily': parameters.raw_pallet_reloc_daily,
            'raw_cboard_reloc_daily': parameters.raw_cboard_reloc_daily,
            'raw_bag_reloc_daily': parameters.raw_bag_reloc_daily,
            'pallet_reloc': parameters.pallet_reloc,
            'container_box_qty': parameters.container_box_qty,
        })

    @api.model
    def check_or_create_analytic_account(self, product):
        AnalyticAccount = self.env['account.analytic.account']
        # Buscar la cuenta analítica con el nombre indicado
        analytic_account = AnalyticAccount.search([
            ('name', '=', product.name),
            ('plan_id', '=', self.env.company.analytic_product_plan_id.id)
        ], limit=1)
        if not analytic_account:
            # Si no existe, crearla
            analytic_account = AnalyticAccount.create({
                'name': product.name,
                'plan_id': self.env.company.analytic_product_plan_id.id
            })
        return analytic_account

    # =========================================================================
    # 1) PICKINGS: HANDLES (Asas)
    # =========================================================================
    picking_in_handles_ids = fields.Many2many(
        'stock.picking',
        relation='analytic_distribution_inplast_handles_rel',  # tabla rel única
        column1='analytic_distribution_id',
        column2='picking_id',
        string="Handle pickings",
        compute="_compute_picking_in_handles_ids",
    )
    picking_in_handles_qty = fields.Float(
        string="Handle pickings qty",
        compute="_compute_picking_in_handles_qty",
    )
    picking_in_pallet_handles_qty = fields.Float(
        string="Handle pallets in",
        compute="_compute_picking_in_handles",
    )

    @api.depends('date_from', 'date_to')
    def _compute_picking_in_handles_ids(self):
        for rec in self:
            pickings = self.env['stock.picking'].search([
                ('scheduled_date', '>=', rec.date_from),
                ('scheduled_date', '<=', rec.date_to),
                ('move_ids_without_package.product_id.categ_id.type', '=', 'handle'),
                ('picking_type_code', '=', 'incoming'),
                ('state', 'in', ['done']),
            ])
            rec.picking_in_handles_ids = pickings

    @api.depends('picking_in_handles_ids')
    def _compute_picking_in_handles_qty(self):
        for rec in self:
            rec.picking_in_handles_qty = len(rec.picking_in_handles_ids)

    @api.depends('date_from', 'date_to')
    def _compute_picking_in_handles(self):
        """Suma el campo 'product_uom_qty' de las líneas de movimientos con productos 'handle'."""
        for rec in self:
            pickings = self.env['stock.picking'].search([
                ('scheduled_date', '>=', rec.date_from),
                ('scheduled_date', '<=', rec.date_to),
                ('move_ids_without_package.product_id.categ_id.type', '=', 'handle'),
                ('picking_type_code', '=', 'incoming'),
                ('state', 'in', ['done']),
            ])
            total_qty = 0.0
            for picking in pickings:
                lines = picking.move_ids_without_package.filtered(
                    lambda l: l.product_id.categ_id.type == 'handle'
                )
                total_qty += sum(lines.mapped('product_uom_qty'))
            rec.picking_in_pallet_handles_qty = total_qty

    # =========================================================================
    # 2) PICKINGS: CAPS (Tapones)
    # =========================================================================
    picking_in_caps_ids = fields.Many2many(
        'stock.picking',
        relation='analytic_distribution_inplast_caps_rel',  # tabla rel única
        column1='analytic_distribution_id',
        column2='picking_id',
        string="Cap pickings",
        compute="_compute_picking_in_caps_ids",
    )
    picking_in_caps_qty = fields.Float(
        string="Cap picking qty",
        compute="_compute_picking_in_caps_qty",
    )
    picking_in_pallet_caps_qty = fields.Float(
        string="Cap pallets received",
        compute="_compute_picking_in_caps",
    )

    @api.depends('date_from', 'date_to')
    def _compute_picking_in_caps_ids(self):
        for rec in self:
            pickings = self.env['stock.picking'].search([
                ('scheduled_date', '>=', rec.date_from),
                ('scheduled_date', '<=', rec.date_to),
                ('move_ids_without_package.product_id.categ_id.type', 'in', ['cap_mrp', 'cap_distribution']),
                ('picking_type_code', '=', 'incoming'),
                ('state', 'in', ['done']),
            ])
            rec.picking_in_caps_ids = pickings

    @api.depends('picking_in_caps_ids')
    def _compute_picking_in_caps_qty(self):
        for rec in self:
            rec.picking_in_caps_qty = len(rec.picking_in_caps_ids)

    @api.depends('date_from', 'date_to')
    def _compute_picking_in_caps(self):
        """Suma el campo 'product_uom_qty' de las líneas de movimientos con productos de tapones."""
        for rec in self:
            pickings = self.env['stock.picking'].search([
                ('scheduled_date', '>=', rec.date_from),
                ('scheduled_date', '<=', rec.date_to),
                ('move_ids_without_package.product_id.categ_id.type', 'in', ['cap_mrp', 'cap_distribution']),
                ('picking_type_code', '=', 'incoming'),
                ('state', 'in', ['done']),
            ])
            total_qty = 0.0
            for picking in pickings:
                lines = picking.move_ids_without_package.filtered(
                    lambda l: l.product_id.categ_id.type in ['cap_mrp', 'cap_distribution']
                )
                total_qty += sum(lines.mapped('product_uom_qty'))
            rec.picking_in_pallet_caps_qty = total_qty

    # =========================================================================
    # 3) SALE ORDERS: CAPS (Tapones)
    # =========================================================================
    sale_caps_order_ids = fields.Many2many(
        'sale.order',
        relation='analytic_distribution_sale_caps_order_rel',  # relación rel única
        column1='analytic_distribution_id',
        column2='sale_order_id',
        string="Orders",
        compute="_compute_sale_caps_order_ids",
    )
    sale_caps_order_count = fields.Integer(
        string="Orders qty",
        compute="_compute_sale_caps_order_count",
    )
    sale_caps_pallet_qty = fields.Float(
        string="Pallet",
        compute="_compute_sale_caps_pallet_qty",
    )
    sale_caps_picking_ids = fields.Many2many(
        'stock.picking',
        relation='analytic_distribution_sale_caps_picking_rel',
        column1='analytic_distribution_id',
        column2='picking_id',
        string="Pickings",
        compute="_compute_sale_caps_picking_ids")
    sale_caps_picking_qty = fields.Float(string="Pickings qty", compute="_compute_sale_caps_picking_qty")
    sale_caps_picking_pallet_qty = fields.Float(string="Pallet pickings qty",
                                                compute="_compute_sale_caps_picking_pallet_qty")

    @api.depends('date_from', 'date_to')
    def _compute_sale_caps_picking_ids(self):
        """Obtiene los pickings del período y filtra aquellos que contengan líneas
        con productos de categoría 'cap_mrp' o 'cap_distribution'."""
        for rec in self:
            pickings = self.env['stock.picking'].search([
                ('scheduled_date', '>=', rec.date_from),
                ('scheduled_date', '<=', rec.date_to),
                ('move_ids_without_package.product_id.categ_id.type', 'in', ['cap_mrp', 'cap_distribution']),
                ('sale_id', 'in', rec.sale_caps_order_ids.ids),
                ('picking_type_code', '=', 'outgoing'),
                ('state', 'in', ['done']),
            ])
            rec.sale_caps_picking_ids = pickings

    @api.depends('sale_caps_picking_ids')
    def _compute_sale_caps_picking_qty(self):
        for rec in self:
            rec.sale_caps_picking_qty = len(rec.sale_caps_picking_ids)

    @api.depends('sale_caps_picking_ids')
    def _compute_sale_caps_picking_pallet_qty(self):
        """Suma el 'product_uom_qty' de las líneas de sale order que tengan
        productos de categoría 'cap_mrp' o 'cap_distribution'."""
        for rec in self:
            total_qty = 0.0
            for so in rec.sale_caps_picking_ids:
                lines = so.move_ids_without_package.filtered(
                    lambda l: l.product_id.categ_id.type in ['cap_mrp', 'cap_distribution']
                )
                total_qty += sum(lines.mapped('product_uom_qty'))
            rec.sale_caps_picking_pallet_qty = total_qty

    @api.depends('date_from', 'date_to')
    def _compute_sale_caps_order_ids(self):
        """Obtiene los sale orders del período y filtra aquellos que contengan líneas
        con productos de categoría 'cap_mrp' o 'cap_distribution'."""
        for rec in self:
            sale_orders = self.env['sale.order'].search([
                ('date_order', '>=', rec.date_from),
                ('date_order', '<=', rec.date_to),
                ('state', 'in', ['sale']),
            ])
            caps_orders = sale_orders.filtered(
                lambda o: any(line.product_id.categ_id.type in ['cap_mrp', 'cap_distribution'] for line in o.order_line)
            )
            rec.sale_caps_order_ids = caps_orders

    @api.depends('sale_caps_order_ids')
    def _compute_sale_caps_order_count(self):
        for rec in self:
            rec.sale_caps_order_count = len(rec.sale_caps_order_ids)

    @api.depends('sale_caps_order_ids')
    def _compute_sale_caps_pallet_qty(self):
        """Suma el 'product_uom_qty' de las líneas de sale order que tengan
        productos de categoría 'cap_mrp' o 'cap_distribution'."""
        for rec in self:
            total_qty = 0.0
            for so in rec.sale_caps_order_ids:
                lines = so.order_line.filtered(
                    lambda l: l.product_id.categ_id.type in ['cap_mrp', 'cap_distribution']
                )
                total_qty += sum(lines.mapped('product_uom_qty'))
            rec.sale_caps_pallet_qty = total_qty

    # =========================================================================
    # 4) SALE ORDERS: HANDLES (Asas)
    # =========================================================================
    sale_handles_order_ids = fields.Many2many(
        'sale.order',
        relation='analytic_distribution_sale_handles_order_rel',  # relación rel única
        column1='analytic_distribution_id',
        column2='sale_order_id',
        string="Handle sale orders",
        compute="_compute_sale_handles_order_ids",
    )
    sale_handles_order_count = fields.Integer(
        string="Handle orders qty",
        compute="_compute_sale_handles_order_count",
    )
    sale_handles_order_qty = fields.Float(
        string="Handle pallets sales",
        compute="_compute_sale_handles_order_qty",
    )

    @api.depends('date_from', 'date_to')
    def _compute_sale_handles_order_ids(self):
        """Obtiene los sale orders del período y filtra aquellos que contengan líneas
        con productos de categoría 'handle'."""
        for rec in self:
            sale_orders = self.env['sale.order'].search([
                ('date_order', '>=', rec.date_from),
                ('date_order', '<=', rec.date_to),
                ('state', 'in', ['sale']),
            ])
            handles_orders = sale_orders.filtered(
                lambda o: any(line.product_id.categ_id.type == 'handle' for line in o.order_line)
            )
            rec.sale_handles_order_ids = handles_orders

    @api.depends('sale_handles_order_ids')
    def _compute_sale_handles_order_count(self):
        for rec in self:
            rec.sale_handles_order_count = len(rec.sale_handles_order_ids)

    @api.depends('sale_handles_order_ids')
    def _compute_sale_handles_order_qty(self):
        """Suma el 'product_uom_qty' de las líneas de sale order que tengan
        productos de categoría 'handle'."""
        for rec in self:
            total_qty = 0.0
            for so in rec.sale_handles_order_ids:
                lines = so.order_line.filtered(
                    lambda l: l.product_id.categ_id.type == 'handle'
                )
                total_qty += sum(lines.mapped('product_uom_qty'))
            rec.sale_handles_order_qty = total_qty

    # =========================================================================
    # 5) PICKINGS: CISTERNAS
    # =========================================================================
    picking_in_cistern_ids = fields.Many2many(
        'stock.picking',
        relation='analytic_distribution_inplast_cistern_rel',
        column1='analytic_distribution_id',
        column2='picking_id',
        string="Cistern pickings",
        compute="_compute_picking_in_cistern_ids",
    )
    picking_in_cistern_qty = fields.Float(
        string="Cistern qty",
        compute="_compute_picking_in_cistern_qty",
    )

    @api.depends('date_from', 'date_to')
    def _compute_picking_in_cistern_ids(self):
        for rec in self:
            pickings = self.env['stock.picking'].search([
                ('scheduled_date', '>=', rec.date_from),
                ('scheduled_date', '<=', rec.date_to),
                ('move_ids_without_package.product_id.categ_id.type', 'in', ['raw_cistern']),
                ('picking_type_code', '=', 'incoming'),
                ('state', 'in', ['done']),
            ])
            rec.picking_in_cistern_ids = pickings

    @api.depends('picking_in_cistern_ids')
    def _compute_picking_in_cistern_qty(self):
        for rec in self:
            rec.picking_in_cistern_qty = len(rec.picking_in_cistern_ids)

    # =========================================================================
    # 6) PICKINGS: SACOS
    # =========================================================================
    picking_in_sack_ids = fields.Many2many(
        'stock.picking',
        relation='analytic_distribution_inplast_sack_rel',
        column1='analytic_distribution_id',
        column2='picking_id',
        string="Sack pickings",
        compute="_compute_picking_in_sack_ids",
    )
    picking_in_sack_qty = fields.Float(
        string="Sack pikings qty",
        compute="_compute_picking_in_sack_qty",
    )

    @api.depends('date_from', 'date_to')
    def _compute_picking_in_sack_ids(self):
        for rec in self:
            pickings = self.env['stock.picking'].search([
                ('scheduled_date', '>=', rec.date_from),
                ('scheduled_date', '<=', rec.date_to),
                ('move_ids_without_package.product_id.categ_id.type', 'in', ['raw_sack']),
                ('picking_type_code', '=', 'incoming'),
                ('state', 'in', ['done']),
            ])
            rec.picking_in_sack_ids = pickings

    @api.depends('picking_in_sack_ids')
    def _compute_picking_in_sack_qty(self):
        for rec in self:
            rec.picking_in_sack_qty = len(rec.picking_in_sack_ids)

    # =========================================================================
    # 7) PICKINGS: COLOR
    # =========================================================================
    picking_in_color_ids = fields.Many2many(
        'stock.picking',
        relation='analytic_distribution_inplast_color_rel',
        column1='analytic_distribution_id',
        column2='picking_id',
        string="Color pickings in",
        compute="_compute_picking_in_color_ids",
    )
    picking_in_color_qty = fields.Float(
        string="Color picking in qty",
        compute="_compute_picking_in_color_qty",
    )

    @api.depends('date_from', 'date_to')
    def _compute_picking_in_color_ids(self):
        for rec in self:
            pickings = self.env['stock.picking'].search([
                ('scheduled_date', '>=', rec.date_from),
                ('scheduled_date', '<=', rec.date_to),
                ('move_ids_without_package.product_id.categ_id.type', 'in', ['raw_color']),
                ('picking_type_code', '=', 'incoming'),
                ('state', 'in', ['done']),
            ])
            rec.picking_in_color_ids = pickings

    @api.depends('picking_in_color_ids')
    def _compute_picking_in_color_qty(self):
        for rec in self:
            rec.picking_in_color_qty = len(rec.picking_in_color_ids)

    # =========================================================================
    # 8) PICKINGS: CARTÓN
    # =========================================================================
    picking_in_cardboard_ids = fields.Many2many(
        'stock.picking',
        relation='analytic_distribution_inplast_cardboard_rel',
        column1='analytic_distribution_id',
        column2='picking_id',
        string="Cardboard pikings",
        compute="_compute_picking_in_cardboard_ids",
    )
    picking_in_cardboard_qty = fields.Float(
        string="Cardboard piking qty",
        compute="_compute_picking_in_cardboard_qty",
    )

    @api.depends('date_from', 'date_to')
    def _compute_picking_in_cardboard_ids(self):
        for rec in self:
            pickings = self.env['stock.picking'].search([
                ('scheduled_date', '>=', rec.date_from),
                ('scheduled_date', '<=', rec.date_to),
                ('move_ids_without_package.product_id.categ_id.type', 'in', ['raw_cardboard']),
                ('picking_type_code', '=', 'incoming'),
                ('state', 'in', ['done']),
            ])
            rec.picking_in_cardboard_ids = pickings

    @api.depends('picking_in_cardboard_ids')
    def _compute_picking_in_cardboard_qty(self):
        for rec in self:
            rec.picking_in_cardboard_qty = len(rec.picking_in_cardboard_ids)

    # =========================================================================
    # 9) PICKINGS: BOLSAS
    # =========================================================================
    picking_in_bag_ids = fields.Many2many(
        'stock.picking',
        relation='analytic_distribution_inplast_bag_rel',
        column1='analytic_distribution_id',
        column2='picking_id',
        string="Bag pickings",
        compute="_compute_picking_in_bag_ids",
    )
    picking_in_bag_qty = fields.Float(
        string="Bag pickings qty",
        compute="_compute_picking_in_bag_qty",
    )

    @api.depends('date_from', 'date_to')
    def _compute_picking_in_bag_ids(self):
        for rec in self:
            pickings = self.env['stock.picking'].search([
                ('scheduled_date', '>=', rec.date_from),
                ('scheduled_date', '<=', rec.date_to),
                ('move_ids_without_package.product_id.categ_id.type', 'in', ['raw_bag']),
                ('picking_type_code', '=', 'incoming'),
                ('state', 'in', ['done']),
            ])
            rec.picking_in_bag_ids = pickings

    @api.depends('picking_in_bag_ids')
    def _compute_picking_in_bag_qty(self):
        for rec in self:
            rec.picking_in_bag_qty = len(rec.picking_in_bag_ids)

    # =========================================================================
    # 10) PICKINGS: pallets
    # =========================================================================

    picking_in_pallet_ids = fields.Many2many(
        'stock.picking',
        relation='analytic_distribution_inplast_pallet_rel',
        column1='analytic_distribution_id',
        column2='picking_id',
        string="Pallet pickings in",
        compute="_compute_picking_in_pallet_ids",
    )
    picking_in_pallet_qty = fields.Float(
        string="Pallet pickings in qty",
        compute="_compute_picking_in_pallet_qty",
    )

    @api.depends('date_from', 'date_to')
    def _compute_picking_in_pallet_ids(self):
        for rec in self:
            pickings = self.env['stock.picking'].search([
                ('scheduled_date', '>=', rec.date_from),
                ('scheduled_date', '<=', rec.date_to),
                ('move_ids_without_package.product_id.categ_id.type', 'in', ['raw_pallet']),
                ('picking_type_code', '=', 'incoming'),
                ('state', 'in', ['done']),
            ])
            rec.picking_in_pallet_ids = pickings

    @api.depends('picking_in_pallet_ids')
    def _compute_picking_in_pallet_qty(self):
        for rec in self:
            rec.picking_in_pallet_qty = len(rec.picking_in_pallet_ids)

    # =========================================================================
    # 11) sale: container
    # =========================================================================

    sale_container_ids = fields.Many2many('sale.order.line', compute='_compute_sale_container_ids',
                                          string='Sale Container')
    sale_container_qty = fields.Integer(string='Cantidad de Container', compute='_compute_sale_container_qty')

    @api.depends('date_from', 'date_to')
    def _compute_sale_container_ids(self):
        for rec in self:
            sales = self.env['sale.order.line'].search([
                ('order_id.date_order', '>=', rec.date_from),
                ('order_id.date_order', '<=', rec.date_to),
                ('state', 'in', ['sale']),
                ('bom_template_type', 'in', ['box', 'box_nonmrp']),
            ])
            parameters = self.env.ref('analytic_distribution_inplast.analytic_distribution_inplast_parameter')
            container_box_qty = parameters.container_box_qty
            sale_line_container = []
            for line in sales:
                if container_box_qty != 0 and (line.product_uom_qty % container_box_qty) == 0:
                    sale_line_container.append(line.id)

            rec.sale_container_ids = [(6, 0, sale_line_container)]

    @api.depends('date_from', 'date_to')
    def _compute_sale_container_qty(self):
        for record in self:
            containers = 0
            parameters = self.env.ref('analytic_distribution_inplast.analytic_distribution_inplast_parameter')
            container_box_qty = parameters.container_box_qty
            for li in record.sale_container_ids:
                containers += li.product_uom_qty / container_box_qty
            record.sale_container_qty = containers

    # =========================================================================
    # MÉTODOS DE CÁLCULO PARA DISTRIBUCIONES ANALÍTICAS:
    # =========================================================================

    """
    def compute_r13(self, li):
        datefrom = self.date_from
        dateto = self.date_to
        total_kwh = 0  # Total de kWh consumidos por todas las máquinas
        workcenters = li.template_id.workcenter_ids
        balance = li.balance  # El coste a distribuir

        # Wororders entre fechas:
        workorders = self.env["mrp.workorder"].search(
            [
                ("workcenter_id", "in", workcenters.ids),
                ("date_start", ">=", datefrom),
                ("date_start", "<=", dateto),
            ]
        )

        # Inicialización de listas simples
        mrpproducts = []
        product_total_kwh = []

        # Cálculo del total de kWh consumidos
        for wo in workorders:
            product = wo.product_id
            duration = wo.duration
            machine = wo.workcenter_id

            # Identificamos productos únicos y agregamos a la lista si no están
            if product not in mrpproducts:
                mrpproducts.append(product)
                product_total_kwh.append(0)  # Inicializamos su consumo total a 0

            # Calculamos el consumo de kWh
            kwh_consumed = duration * machine.power_kw
            total_kwh += kwh_consumed

            # Actualizamos el consumo total por producto
            product_index = mrpproducts.index(product)
            product_total_kwh[product_index] += kwh_consumed

        # Verificar si hay consumo total de kWh para evitar la división por cero
        if total_kwh == 0:
            raise UserError("No hay consumo de energía registrado.")

        # Crear entradas analíticas para cada producto
        for i in range(len(mrpproducts)):
            product = mrpproducts[i]
            product_kwh = product_total_kwh[i]

            machine_percentage = (product_kwh / total_kwh) * 100
            machine_cost = (balance * machine_percentage) / 100

            # Buscar la cuenta analítica para el producto base tapón, o crearla:
            analytic_product = product
            if product.pnt_product_type == 'packing':
                analytic_product = product.pnt_parent_id

            analytic_account = self.env['account.analytic.account'].search([
                ('product_id','=',analytic_product.id)
            ])
            if not analytic_account.id:
                analytic_account = self.env['account.analytic.account'].create({
                    'product_id': analytic_product.id,
                    'plan_id': self.env.company.analytic_product_plan_id.id,
                    'name': analytic_product.name,
                })

            # Buscar el nombre del campo creado dinámicamente:
            analytic_field_name = self.env['ir.model.fields'].search([
                ('model','=','account.analytic.line'),
                ('ttype','=','many2one'),
                ('field_description','=',analytic_account.plan_id.name),
            ]).name

            self.env["account.analytic.line"].create(
                {
                    "name": f"Consumo {product.name}",
                    "amount": machine_cost,
                    "product_id": product.id,
                    "date": fields.Date.today(),
                    "analytic_distribution_id": self.id,
                    analytic_field_name: analytic_account.id,
                }
            )

        return True

    def compute_r14(self):
        datefrom = self.date_from
        dateto = self.date_to
        total_duration = 0  # Total de kWh consumidos por todas las máquinas
        workcenters = self.workcenter_ids
        amount = self.amount  # El máximo coste a distribuir

        # Órdenes de manufactura consideradas entre fechas:
        workorders = self.env["mrp.workorder"].search(
            [
                ("workcenter_id", "in", workcenters.ids),
                ("date_start", ">=", datefrom),
                ("date_start", "<=", dateto),
            ]
        )

        # Inicialización de listas simples
        mrpproducts = []
        product_total_duration = []

        # Cálculo del total de kWh consumidos
        for wo in workorders:
            product = wo.product_id
            duration = wo.duration
            machine = wo.workcenter_id

            # Identificamos productos únicos y agregamos a la lista si no están
            if product not in mrpproducts:
                mrpproducts.append(product)
                product_total_duration.append(0)  # Inicializamos su consumo total a 0

            total_duration += duration

            # Actualizamos el consumo total por producto
            product_index = mrpproducts.index(product)
            product_total_duration[product_index] += duration

        # Verificar si hay consumo total de kWh para evitar la división por cero
        if total_duration == 0:
            raise UserError("No hay consumo de energía registrado.")

        # Crear entradas analíticas para cada producto
        for i in range(len(mrpproducts)):
            product = mrpproducts[i]
            product_kwh = product_total_duration[i]

            machine_percentage = (product_kwh / total_duration) * 100
            machine_cost = (amount * machine_percentage) / 100

            self.env["account.analytic.line"].create(
                {
                    "name": f"Consumo {product.name}",
                    "amount": machine_cost,
                    "product_id": product.id,
                    "date": fields.Date.today(),
                    "analytic_distribution_id": self.id,
                }
            )

        return True

    def compute_r22(self):
        # El chequeo de región es el siguiente: país = España (ES), o posición fiscal "intracomuntaria" (EU) y otros.
        # La parametrización está hecha:
        analytic_spain = self.env.company.analytic_spain_account_id.id
        analytic_eu= self.env.companyanalytic_eu_account_id.id
        analytic_noneu = self.env.company.analytic_non_eu_account_id.id
        amount = self.amount

        fiscal_position_eu_external_id = "account." + self.company.id + "_" + "fp_intra"
        partner_eu = self.env.ref(fiscal_position_eu_external_id)

        if not analytic_spain.id or not analytic_eu.id or not analytic_noneu.id:
            raise UserError('Go to company => Analytic parametrization and assign region accounts.')

        # Cálculo para España: Todos los account.move.line de las cuentas, cuyo partner.country_id es España.
        #  Es UE si la posición fiscal es partner_eu.id; el resto a "Resto del mundo".

        #  Se hace el porcentaje sobre el total de venta,
        #  Se crea array de familia que ha sido cada venta (por array de venta, familia),
        #  Si existe cuenta analítica para esta familia, se añade apunte contable, en otro caso se crea y después añade.

        # El array podría ser: [ 'region', 'familia' , 'importe']
        # Después calcular en base al array.
        return True
    """
