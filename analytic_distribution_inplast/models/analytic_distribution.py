# -*- coding: utf-8 -*-
# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models, api
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class AnalyticDistribution(models.Model):
    _inherit = 'analytic.distribution'


    picking_hour_qty = fields.Float(string='Pickig hours',compute='_compute_picking_hour_qty')
    @api.depends('date_from', 'date_to')
    def _compute_picking_hour_qty(self):
        for rec in self:
            parameters = self.env.ref('analytic_distribution_inplast.analytic_distribution_inplast_parameter')
            # R1: Descarga de tapones y asas en la central (nº de albaranes):
            caps_handle_picking_unload = (rec.picking_in_caps_qty + rec.picking_in_handles_qty) * rec.picking_unload
            # R2: Traslado desde producción a STOCK:
            mrp2stock_picking = rec.picking_mrp2stock_hour * rec.pallet_reloc / 60
            # R3: Carga manual de contenedores, ya que ocupan mucho tiempo:
            container_load = rec.move_container_qty * rec.container_load
            # R3.1: Carga de tapones y asas en la central (nº de albaranes):
            # (previo por horas, he pasado a minutos el 26/03/25) caps_handle_picking_load = (distribution.sale_caps_picking_qty + distribution.sale_handles_picking_qty) * parameters.truck_load
            caps_handle_picking_load = (rec.sale_caps_picking_pallet_qty) * rec.pallet_reloc / 60

            # R4: Recepción y pesaje de materiales (materias primas y embalajes):
            cistern_unload = rec.raw_cistern_unload * rec.picking_in_cistern_qty
            sack_unload = rec.raw_sack_unload * rec.picking_in_sack_qty
            color_unload = rec.raw_color_unload * rec.picking_in_color_qty
            cardboard_unload = rec.raw_cardboard_unload * rec.picking_in_cardboard_qty
            bag_unload = rec.raw_bag_unload * rec.picking_in_bag_qty
            pallet_unload = rec.raw_pallet_unload * rec.picking_in_pallet_qty
            r4 = cistern_unload + sack_unload + color_unload + cardboard_unload + bag_unload + pallet_unload

            # R5.- Movimientos de materia prima a producción:
            stk2mrp_pickings = rec.days * (rec.raw_color_reloc_daily + rec.raw_cboard_reloc_daily + rec.raw_bag_reloc_daily + rec.raw_pallet_reloc_daily)

            rec.picking_hour_qty = (
                    caps_handle_picking_unload +
                    mrp2stock_picking +
                    container_load +
                    caps_handle_picking_load +
                    r4 +
                    stk2mrp_pickings
            )

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
            li.compute_debit_credit()
            if li.template_id.compute_method == "demo":
                a = 1
                # raise UserError("ok")
            elif li.template_id.compute_method == "r1":
                self.compute_r1(li)
            elif li.template_id.compute_method == "r2":
                self.compute_r2(li)
            elif li.template_id.compute_method == "r3":
                self.compute_r3(li)
            elif li.template_id.compute_method == "r3.1":
                self.compute_r31(li)
            elif li.template_id.compute_method == "r4":
                self.compute_r4(li)
            elif li.template_id.compute_method == "r5":
                self.compute_r5(li)
            elif li.template_id.compute_method == "r6":
                self.compute_r6(li)
            elif li.template_id.compute_method == "r7":
                self.compute_r7(li)
            elif li.template_id.compute_method in ["r8", "r9"]:
                self.compute_r8r9(li)
            elif li.template_id.compute_method in ["r10", "r11", "r14", "r15"]:
                self.compute_r10r11(li)
            elif li.template_id.compute_method in ["r10_legacy", "r11_legacy", "r14_legacy", "r15_legacy"]:
                self.compute_r10r11_legacy(li)
            elif li.template_id.compute_method == "r12":
                self.compute_r12(li)
            elif li.template_id.compute_method == "r12_legacy":
                self.compute_r12_legacy(li)
            elif li.template_id.compute_method == "r13":
                self.compute_r13(li)
            elif li.template_id.compute_method == "r13_legacy":
                self.compute_r13_legacy(li)
            elif li.template_id.compute_method == "r16":
                self.compute_r16(li)
            elif li.template_id.compute_method == "r16_legacy":
                self.compute_r16_legacy(li)
            elif li.template_id.compute_method == "r16.1":
                self.compute_r161(li)
            elif li.template_id.compute_method == "r16.1_legacy":
                self.compute_r161_legacy(li)
            elif li.template_id.compute_method == "r18":
                self.compute_r18(li)
            elif li.template_id.compute_method == "r18.1":
                self.compute_r181(li)
            elif li.template_id.compute_method == "r19":
                self.compute_r19(li)
            elif li.template_id.compute_method == "r20":
                self.compute_r20(li)
            elif li.template_id.compute_method == "r21":
                self.compute_r21(li)
            elif li.template_id.compute_method == "r22":
                self.compute_r22(li)
            elif li.template_id.compute_method == "r23":
                self.compute_r23(li)

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
    purchase_estimation = fields.Float(
        string='Purchase time %',
        help='Estimated purchase % time'
    )
    purchase_estimation_handle = fields.Float(
        string='Handle purchase %',
        help='Estimated purchase % time'
    )
    mrp_maintenance_time = fields.Float(
        string='MRP issues %h',
        help='% de horas de mantenimiento que se consideran sobre el periodo de producción efectivo. Por ejemplo si se considera un 20% de mantenimiento y paradas durante el tiempo productivo, aquí indicaremos 20'
    )
    sale_palet_estimation = fields.Float(
        string='Sale palets %',
        help='Estimated sale palets % time'
    )
    sale_estimation = fields.Float(
        string='Sales time %',
        help='Estimated sales % time'
    )
    sale_mrp_estimation = fields.Float(
        string='Sale MRP time %',
        help='Estimated sale MRP % time'
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
            'purchase_estimation': parameters.purchase_estimation,
            'purchase_estimation_handle': parameters.purchase_estimation_handle,
            'mrp_maintenance_time': parameters.mrp_maintenance_time,
            'sale_palet_estimation': parameters.sale_palet_estimation,
            'sale_estimation': parameters.sale_estimation,
            'sale_mrp_estimation': parameters.sale_mrp_estimation,
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
        compute="_compute_picking_in_pallet_handles_qty",
    )
    picking_in_pallet_handles_hour = fields.Float(
        string="Picking in pallet handles Hours",
        compute="_compute_picking_in_pallet_handles_hour"
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
    def _compute_picking_in_pallet_handles_qty(self):
        """Suma el campo 'product_uom_qty' de las líneas de movimientos con productos 'handle'."""
        for rec in self:
            pickings = rec.picking_in_handles_ids
            total_qty = 0.0
            for picking in pickings:
                lines = picking.move_ids_without_package.filtered(
                    lambda l: l.product_id.categ_id.type == 'handle' and l.product_id.pnt_product_type == 'packing'
                )
                total_qty += sum(lines.mapped('product_uom_qty'))
            rec.picking_in_pallet_handles_qty = total_qty

    @api.depends('date_from', 'date_to')
    def _compute_picking_in_pallet_handles_hour(self):
        """Horas empleadas."""
        for rec in self:
            rec.picking_in_pallet_handles_hour = rec.picking_in_handles_qty * rec.picking_unload


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
        compute="_compute_picking_in_pallet_caps_qty",
    )
    picking_in_pallet_caps_hour = fields.Float(
        string="Picking in pallet caps Hours",
        compute="_compute_picking_in_pallet_caps_hour",
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
    def _compute_picking_in_pallet_caps_qty(self):
        """Suma el campo 'product_uom_qty' de las líneas de movimientos con productos de tapones."""
        for rec in self:
            pickings = rec.picking_in_caps_ids
            total_qty = 0.0
            for picking in pickings:
                lines = picking.move_ids_without_package.filtered(
                    lambda l: l.product_id.categ_id.type in ['cap_mrp', 'cap_distribution'] and l.product_id.pnt_product_type == 'packing'
                )
                total_qty += sum(lines.mapped('product_uom_qty'))
            rec.picking_in_pallet_caps_qty = total_qty

    @api.depends('date_from', 'date_to')
    def _compute_picking_in_pallet_caps_hour(self):
        """Horas empleadas."""
        for rec in self:
            rec.picking_in_pallet_caps_hour = rec.picking_in_caps_qty * rec.picking_unload

    # MRP TO STOCK PICKINGS:
    picking_mrp2stock_ids = fields.Many2many(
        'stock.picking',
        string="Pickings",
        help="MRP to stock pickings",
        compute="_compute_picking_mrp2stock_ids",
    )
    picking_mrp2stock_qty = fields.Float(
        string="Pickings qty",
        help="MRP to stock picking qty",
        compute="_compute_picking_mrp2stock_qty",
    )
    picking_mrp2stock_pallets_qty = fields.Float(
        string="Pallets",
        compute="_compute_picking_mrp2stock_pallets_qty"
    )
    picking_mrp2stock_hour = fields.Float(
        string="Picking MRP2Stock Hours",
        compute="_compute_picking_mrp2stock_hours"
    )
    @api.depends('date_from', 'date_to')
    def _compute_picking_mrp2stock_ids(self):
        pickings = self.env['mrp.production'].search([
            ('date_finished', '>=', self.date_from),
            ('date_finished', '<=', self.date_to),
            ('state','in',['done']),
            ('incoming_picking','!=',False),
            ('product_id.mrp_bom_template_id.type','=','pallet')
        ]).incoming_picking
        self.picking_mrp2stock_ids = [(6,0,pickings.ids)]

    @api.depends('picking_mrp2stock_ids')
    def _compute_picking_mrp2stock_qty(self):
        self.picking_mrp2stock_qty = len(self.picking_mrp2stock_ids)

    @api.depends('picking_mrp2stock_ids')
    def _compute_picking_mrp2stock_pallets_qty(self):
        # Total palets en albarán (no incluyo 'cap_distribution' porque esos no vienen de fábrica):
        total_pallets = 0
        for picking in self.picking_mrp2stock_ids:
            lines = picking.move_ids_without_package.filtered(
                lambda l: l.product_id.categ_id.type in ['cap_mrp'] and l.product_id.pnt_product_type == 'packing'
            )
            total_pallets += sum(lines.mapped('product_uom_qty'))
        self.picking_mrp2stock_pallets_qty = total_pallets

    @api.depends('picking_mrp2stock_pallets_qty')
    def _compute_picking_mrp2stock_hours(self):
        self.picking_mrp2stock_hour = self.picking_mrp2stock_pallets_qty * self.pallet_reloc / 60

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
        compute="_compute_sale_caps_picking_ids",
        help="Albaranes de salida de tapones en el periodo especificado; sin pertencia a pedidos cerrados en esa fecha, "
             "para incluir anteriores que se sirven ahora"
    )
    sale_caps_picking_qty = fields.Float(string="Pickings qty", compute="_compute_sale_caps_picking_qty")
    sale_caps_picking_pallet_qty = fields.Float(string="Pallet pickings qty",
                                                compute="_compute_sale_caps_picking_pallet_qty")

    @api.depends('date_from', 'date_to')
    def _compute_sale_caps_picking_ids(self):
        """Obtiene los pickings del período y filtra aquellos que contengan líneas
        con productos de categoría 'cap_mrp' o 'cap_distribution'."""
        for rec in self:
            moves = self.env['stock.move'].search([
                ('picking_id.date_done', '>=', rec.date_from),
                ('picking_id.date_done', '<=', rec.date_to),
                ('picking_id.picking_type_code', '=', 'outgoing'),
                ('state', 'in', ['done']),
                ('product_id.categ_id.type', 'in', ['cap_mrp', 'cap_distribution']),
                ('product_id.mrp_bom_template_id.type', 'in', ['pallet', 'pallet_nonmrp']),
                ('product_uom_qty', '>', 0),
            ])
            pickings = moves.picking_id

            """ 26/03/25 quitado por moves
            pickings = self.env['stock.picking'].search([
                ('scheduled_date', '>=', rec.date_from),
                ('scheduled_date', '<=', rec.date_to),
                ('move_ids_without_package.product_id.categ_id.type', 'in', ['cap_mrp', 'cap_distribution']),
                ('picking_type_code', '=', 'outgoing'),
                ('state', 'in', ['done']),
            ])
            """
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
                              and l.product_id.pnt_product_type == 'packing'
                              and l.product_id.mrp_bom_template_id.type in ['pallet','pallet_nonmrp']
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
                lambda o: any(line.product_id.categ_id.type in ['cap_mrp', 'cap_distribution']
                              and line.product_id.pnt_product_type == 'packing'
                              for line in o.order_line)
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
                    lambda l: l.product_id.categ_id.type in ['cap_mrp', 'cap_distribution'] and l.product_id.pnt_product_type == 'packing'
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

    sale_handles_picking_ids = fields.Many2many(
        'stock.picking',
        relation='analytic_distribution_sale_handles_picking_rel',
        column1='analytic_distribution_id',
        column2='picking_id',
        string="Pickings",
        compute="_compute_sale_handles_picking_ids")

    sale_handles_picking_qty = fields.Float(
        string="Pickings qty",
        compute="_compute_sale_handles_picking_qty"
    )

    sale_handles_picking_pallet_qty = fields.Float(
        string="Pallet pickings qty",
        compute="_compute_sale_handles_picking_pallet_qty"
    )

    @api.depends('date_from', 'date_to')
    def _compute_sale_handles_picking_ids(self):
        """Obtiene los pickings del período y filtra aquellos que contengan líneas
        con productos de categoría 'handle'."""
        for rec in self:
            moves = self.env['stock.move'].search([
                ('picking_id.date_done', '>=', rec.date_from),
                ('picking_id.date_done', '<=', rec.date_to),
                ('picking_id.picking_type_code', '=', 'outgoing'),
                ('state', 'in', ['done']),
                ('product_id.categ_id.type', 'in', ['handle']),
                ('product_id.mrp_bom_template_id.type', 'in', ['pallet', 'pallet_nonmrp']),
                ('product_uom_qty', '>', 0),
            ])
            pickings = moves.picking_id
            rec.sale_handles_picking_ids = pickings

    @api.depends('sale_handles_picking_ids')
    def _compute_sale_handles_picking_qty(self):
        for rec in self:
            rec.sale_handles_picking_qty = len(rec.sale_handles_picking_ids)


    @api.depends('sale_handles_picking_ids')
    def _compute_sale_handles_picking_pallet_qty(self):
        """Suma el 'product_uom_qty' de las líneas de sale order que tengan
        productos de categoría 'handle'."""
        for rec in self:
            total_qty = 0.0
            for so in rec.sale_handles_picking_ids:
                lines = so.move_ids_without_package.filtered(
                    lambda l: l.product_id.categ_id.type in ['handle'] and l.product_id.pnt_product_type == 'packing'
                )
                total_qty += sum(lines.mapped('product_uom_qty'))
            rec.sale_handles_picking_pallet_qty = total_qty





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
                lambda o: any(line.product_id.categ_id.type == 'handle'
                              and line.product_id.pnt_product_type == 'packing'
                              for line in o.order_line)
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
                    lambda l: l.product_id.categ_id.type == 'handle' and l.product_id.pnt_product_type == 'packing'
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
    picking_in_cistern_hour = fields.Float(
        string="Picking in cistern Hours",
        compute="_compute_picking_in_cistern_hours",
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

    @api.depends('picking_in_cistern_qty')
    def _compute_picking_in_cistern_hours(self):
        """Horas empleadas."""
        for rec in self:
            rec.picking_in_cistern_hour = rec.picking_in_cistern_qty * rec.raw_cistern_unload

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
    picking_in_sack_hour = fields.Float(
        string="Picking in sack Hours",
        compute="_compute_picking_in_sack_hours",
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

    @api.depends('picking_in_sack_qty')
    def _compute_picking_in_sack_hours(self):
        """Horas empleadas."""
        for rec in self:
            rec.picking_in_sack_hour = rec.picking_in_sack_qty * rec.raw_sack_unload

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
    picking_in_color_hour = fields.Float(
        string="Picking in color Hours",
        compute="_compute_picking_in_color_hours",
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

    @api.depends('picking_in_color_qty')
    def _compute_picking_in_color_hours(self):
        """Horas empleadas."""
        for rec in self:
            rec.picking_in_color_hour = rec.picking_in_color_qty * rec.raw_color_unload

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
    picking_in_cardboard_hour = fields.Float(
        string="Picking in cardboard Hours",
        compute="_compute_picking_in_cardboard_hours",
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

    @api.depends('picking_in_cardboard_qty')
    def _compute_picking_in_cardboard_hours(self):
        """Horas empleadas."""
        for rec in self:
            rec.picking_in_cardboard_hour = rec.picking_in_cardboard_qty * rec.raw_cardboard_unload

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
    picking_in_bag_hour = fields.Float(
        string="Picking in bag Hours",
        compute="_compute_picking_in_bag_hours",
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

    @api.depends('picking_in_bag_qty')
    def _compute_picking_in_bag_hours(self):
        """Horas empleadas."""
        for rec in self:
            rec.picking_in_bag_hour = rec.picking_in_bag_qty * rec.raw_bag_unload

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
    picking_in_pallet_hour = fields.Float(
        string="Picking in pallet Hours",
        compute="_compute_picking_in_pallet_hours",
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

    @api.depends('picking_in_pallet_qty')
    def _compute_picking_in_pallet_hours(self):
        """Horas empleadas."""
        for rec in self:
            rec.picking_in_pallet_hour = rec.picking_in_pallet_qty * rec.raw_pallet_unload

    # =========================================================================
    # 11) sale: container
    # =========================================================================

    sale_container_ids = fields.Many2many('sale.order.line',
                                          compute='_compute_sale_container_ids',
                                          string='Sale Container')
    sale_container_qty = fields.Integer(string='Contenedores', compute='_compute_sale_container_qty')
    move_container_ids = fields.Many2many('stock.move', string='Container moves', compute='_compute_stock_move_container')
    move_container_qty = fields.Float(string='Containers pickings qty', compute='_compute_move_container_qty')
    move_container_hour = fields.Float(string='Move container Hours', compute='_compute_move_container_hour')

    @api.depends('date_from', 'date_to')
    def _compute_sale_container_ids(self):
        for rec in self:
            # ESTO NO VALE PORQUE NO SON LOS SERVIDOS, SON LOS VENDIDOS:
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


    @api.depends('date_from', 'date_to')
    def _compute_stock_move_container(self):
        for rec in self:
            moves = self.env['stock.move'].search([
                ('sale_line_id', '!=', False),
                ('state','in',['done']),
                ('picking_id.date_done','>=',rec.date_from),
                ('picking_id.date_done','<=',rec.date_to),
                ('product_id.mrp_bom_template_id.type', 'in', ['box', 'box_nonmrp']),
                ('picking_id.picking_type_code','=','outgoing'),
                ('product_uom_qty','>',0),
            ])

            # Filtrar por número de cajas por contenedor indicado en parametrización:
            parameters = self.env.ref('analytic_distribution_inplast.analytic_distribution_inplast_parameter')
            container_box_qty = parameters.container_box_qty
            move_container = []
            for line in moves:
                if container_box_qty != 0 and (line.product_uom_qty % container_box_qty) == 0:
                    move_container.append(line.id)

            rec.move_container_ids = move_container

    @api.depends('move_container_ids')
    def _compute_move_container_qty(self):
        for rec in self:
            containers = 0
            parameters = self.env.ref('analytic_distribution_inplast.analytic_distribution_inplast_parameter')
            container_box_qty = parameters.container_box_qty
            for li in rec.move_container_ids:
                containers += li.product_uom_qty / container_box_qty
            rec.move_container_qty = containers

    @api.depends('move_container_qty')
    def _compute_move_container_hour(self):
        for record in self:
            record.move_container_hour = record.move_container_qty * record.container_load

