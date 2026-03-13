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
            elif li.template_id.compute_method == "r12":
                self.compute_r12(li)
            elif li.template_id.compute_method == "r13":
                self.compute_r13(li)
            elif li.template_id.compute_method == "r18":
                self.compute_r18(li)
            elif li.template_id.compute_method == "r18.1":
                self.compute_r181(li)
            elif li.template_id.compute_method == "r22":
                self.compute_r22(li)
            elif li.template_id.compute_method == "r23":
                self.compute_r23(li)

    ###########################################
    # R1: Descarga y ubicación de ASAS.
    # Un apunte por producto ASA.
    ###########################################
    def compute_r1(self, li):
        for rec in self:
            pickings = rec.picking_in_handles_ids
            moves = self.env['stock.move'].search([
                ('picking_id','in',pickings.ids),
                ('product_id.mrp_bom_template_id.type', 'in',['pallet','pallet_nonmrp']),
                ('product_id.categ_id.type','=', 'handle' ),
                ('product_uom_qty', '>', 0),
            ])
            products = moves.product_id.pnt_parent_id
            # Para realizar un sólo apunte por producto base:
            for product in products:
                picking_cost = 0
                lines = moves.filtered(lambda l: l.product_id.pnt_parent_id == product)
                product_pickings = lines.picking_id
                # Para el reparto proporcional por albarán:
                for picking in product_pickings:
                    # Total de pallets a descargar (de todos los modelos de asas y de este en particular):
                    handles_lines = picking.move_ids_without_package.filtered(
                        lambda l: l.product_id.categ_id.type == 'handle'
                                  and l.product_id.pnt_product_type == 'packing'
                    )
                    product_lines = picking.move_ids_without_package.filtered(
                        lambda l: l.product_id.categ_id.type == 'handle'
                                  and l.product_id.pnt_product_type == 'packing'
                                  and l.product_id.pnt_parent_id == product
                    )
                    # Proporción del coste en función del nº de pallets del producto:
                    total_picking_pallets = sum(handles_lines.mapped('product_uom_qty'))
                    product_picking_pallets = sum(product_lines.mapped('product_uom_qty'))
                    picking_time = rec.picking_unload * (product_picking_pallets / total_picking_pallets)
                    picking_cost += picking_time * li.picking_hour_cost

                # Buscamos si ya existe o se crea la cuenta analítica para este producto:
                analytic_account = self.check_or_create_analytic_account(product)
                # Creación del apunte analítico:
                product_field_id = self.env.company.product_field_id.name
                fixed_variable_field_id = self.env.company.fixed_variable_field_id.name
                machine_field_id = self.env.company.machine_field_id.name
                department_field_id = self.env.company.department_field_id.name
                # Albaranes correspondientes al apunte analítico:
                picking_names = "[ "
                for picking in product_pickings:
                    picking_names += picking.name + " "
                picking_names += "]"

                new_aal = self.env['account.analytic.line'].create({
                    'product_id': product.id,
                    'name': li.template_id.name + " - " + rec.name + " " + picking_names,
                    'amount': -1 * abs(picking_cost),
                    product_field_id: analytic_account.id,
                    fixed_variable_field_id: self.env.company.analytic_variable_account_id.id,
                    department_field_id: self.env.company.analytic_warehouse_department_id.id,
                    'analytic_distribution_id': self.id,
                    'analytic_distribution_template_id': li.template_id.id,
                })


    ###########################################
    # R2: Recogida de palets de tapones y ubicación.
    ###########################################
    def compute_r2(self, li):
        for rec in self:
            pickings = rec.picking_mrp2stock_ids
            moves = self.env['stock.move'].search([
                ('id','in',pickings.move_ids_without_package.ids),
                ('product_id.mrp_bom_template_id.type', '=','pallet'),
            ])
            products = moves.product_id.pnt_parent_id
            # Para realizar un sólo apunte por producto base:
            for product in products:
                lines = moves.filtered(lambda l: l.product_id.pnt_parent_id == product)
                product_pickings = lines.picking_id
                total_pallets = sum(lines.mapped('product_uom_qty'))
                picking_names = "[ "
                for picking in product_pickings:
                    picking_names += picking.name + " "
                picking_names += "]"
                picking_cost = total_pallets * li.picking_hour_cost * rec.pallet_reloc / 60
                # Buscamos si ya existe o se crea la cuenta analítica para este producto:
                analytic_account = self.check_or_create_analytic_account(product)
                # Creamos el apunte analítico:
                product_field_id = self.env.company.product_field_id.name
                fixed_variable_field_id = self.env.company.fixed_variable_field_id.name
                department_field_id = self.env.company.department_field_id.name
                new_aal = self.env['account.analytic.line'].create({
                    'product_id': product.id,
                    'name': li.template_id.name + " - " + rec.name + " " + picking_names,
                    'amount': -1 * abs(picking_cost),
                    product_field_id: analytic_account.id,
                    fixed_variable_field_id: self.env.company.analytic_variable_account_id.id,
                    department_field_id: self.env.company.analytic_warehouse_department_id.id,
                    'analytic_distribution_id': self.id,
                    'analytic_distribution_template_id': li.template_id.id,
                })


    ###########################################
    # R3: Carga Contenedor de cajas.
    ###########################################
    def compute_r3(self, li):
        # Albaranes que tienen múltiplos de las cajas por contenedor indicadas en la parametrización:
        for rec in self:
            moves = rec.move_container_ids
            # Recorremos por producto para hacer un único apunte R3 por cada cuenta analítica:
            pickings = moves.picking_id
            products = moves.product_id.pnt_parent_id
            for product in products:
                lines = moves.filtered(lambda l: l.product_id.pnt_parent_id == product)
                # Nombre del apunte analítico:
                pickings = lines.picking_id
                picking_names = "[ "
                for picking in pickings: picking_names += picking.name + " "
                picking_names += "]"
                # Cada SM es un contenedor.
                total_containers = len(lines)
                # Buscamos si ya existe o se crea la cuenta analítica para este producto:
                analytic_account = self.check_or_create_analytic_account(product)

                product_field_id = self.env.company.product_field_id.name
                fixed_variable_field_id = self.env.company.fixed_variable_field_id.name
                machine_field_id = self.env.company.machine_field_id.name
                department_field_id = self.env.company.department_field_id.name

                new_aal = self.env['account.analytic.line'].create({
                    'product_id': product.id,
                    'name': li.template_id.name + " - " + rec.name + " " + picking_names,
                    'amount': - rec.container_load * li.picking_hour_cost * total_containers,
                    product_field_id: analytic_account.id,
                    fixed_variable_field_id: self.env.company.analytic_variable_account_id.id,
                    department_field_id: self.env.company.analytic_warehouse_department_id.id,
                    'analytic_distribution_id': self.id,
                    'analytic_distribution_template_id': li.template_id.id,
                })

    ###########################################
    # R3.1: Desubicación y carga: Se miran los albaranes de salida (no utilizan playa) de Tapones y asas.
    # El coste es calculado por el precio por minuto.
    ###########################################
    def compute_r31(self, li):
        for rec in self:
            moves = self.env['stock.move'].search([
                ('picking_id.date_done', '>=', rec.date_from),
                ('picking_id.date_done', '<=', rec.date_to),
                ('picking_id.picking_type_code', '=', 'outgoing'),
                ('state', 'in', ['done']),
                ('product_id.mrp_bom_template_id.type', 'in', ['pallet', 'pallet_nonmrp']),
                ('product_uom_qty', '>', 0),
            ])
            pickings = moves.picking_id
            products = moves.product_id.pnt_parent_id
            for product in products:
                lines = moves.filtered(lambda l: l.product_id.pnt_parent_id == product)
                pickings = lines.picking_id
                picking_names = "[ "
                for picking in pickings: picking_names += picking.name + " "
                picking_names += "]"
                total_pallets = sum(lines.mapped('product_uom_qty'))
                picking_cost = total_pallets * li.picking_hour_cost * rec.pallet_reloc / 60
                # Buscamos si ya existe o se crea la cuenta analítica para este producto:
                analytic_account = self.check_or_create_analytic_account(product)
                product_field_id = self.env.company.product_field_id.name
                fixed_variable_field_id = self.env.company.fixed_variable_field_id.name
                department_field_id = self.env.company.department_field_id.name
                new_aal = self.env['account.analytic.line'].create({
                    'product_id': product.id,
                    'name': li.template_id.name + " - " + rec.name + " " + picking_names,
                    'amount': -1 * abs(picking_cost),
                    product_field_id: analytic_account.id,
                    fixed_variable_field_id: self.env.company.analytic_variable_account_id.id,
                    department_field_id: self.env.company.analytic_warehouse_department_id.id,
                    'analytic_distribution_id': self.id,
                    'analytic_distribution_template_id': li.template_id.id,
                })

    ###########################################
    # R4: Recepción y pesaje de materiales: Según si tipo de materia prima se estipula un tiempo de recepción.
    # Coste por precio hora almacén. Se estiman albaranes completos de tipo de materia prima con distintos modelos.
    ###########################################
    def compute_r4(self, li):
        for rec in self:
            categ_types = ['raw_cistern', 'raw_sack', 'raw_pallet', 'raw_bag', 'raw_cardboard', 'raw_color']
            types = [
                ['raw_cistern', rec.raw_cistern_unload],
                ['raw_sack', rec.raw_sack_unload],
                ['raw_pallet', rec.raw_pallet_unload],
                ['raw_bag', rec.raw_bag_unload],
                ['raw_cardboard', rec.raw_cardboard_unload],
                ['raw_color', rec.raw_color_unload]
            ]
            # Recorremos los tipos posibles de encontrar, con su estimacion de tiempos por tipo según la tabla anterior:
            for type in types:
                moves = self.env['stock.move'].search([
                    ('picking_id.date_done', '>=', rec.date_from),
                    ('picking_id.date_done', '<=', rec.date_to),
                    ('picking_id.picking_type_code', '=', 'incoming'),
                    ('state', 'in', ['done']),
                    ('product_id.categ_id.type', '=', type[0]),
                    ('product_uom_qty', '>', 0),
                ])
                products = moves.product_id

                # Recorremos por producto para hacer un único apunte R4 por cada cuenta analítica:
                for product in products:
                    product_moves = self.env['stock.move'].search([
                        ('id', 'in', moves.ids),
                        ('product_id', '=', product.id),
                    ])
                    # este reparto está mal, hay que tener el importe estimado por días total del mes,

                    # Reparto proporcional por si un albarán lleva varios productos [len(picking_moves)]
                    product_pickings = product_moves.picking_id
                    picking_cost = 0
                    for pi in product_pickings:
                        picking_moves = self.env['stock.move'].search([
                            ('picking_id', '=', pi.id),
                            ('product_id.categ_id.type', 'in', categ_types),
                        ]).product_id
                        picking_cost += li.picking_hour_cost * type[1] / len(picking_moves)

                    # Nombre del apunte analítico:
                    picking_names = "[ "
                    for product_picking in product_pickings: picking_names += product_picking.name + " "
                    picking_names += "]"

                    # Buscamos si ya existe o se crea la cuenta analítica para este producto:
                    analytic_account = self.check_or_create_analytic_account(product)

                    # Creación del apunte analítico:
                    product_field_id = self.env.company.product_field_id.name
                    fixed_variable_field_id = self.env.company.fixed_variable_field_id.name
                    department_field_id = self.env.company.department_field_id.name
                    new_aal = self.env['account.analytic.line'].create({
                        'product_id': product.id,
                        'name': li.template_id.name + " - " + rec.name + " " + picking_names,
                        'amount': -1 * abs(picking_cost),
                        product_field_id: analytic_account.id,
                        fixed_variable_field_id: self.env.company.analytic_variable_account_id.id,
                        department_field_id: self.env.company.analytic_warehouse_department_id.id,
                        'analytic_distribution_id': self.id,
                        'analytic_distribution_template_id': li.template_id.id,
                    })

    ###########################################
    # R5: Aprovisionamiento materiales producción.
    # Kg totales por artículos y tipo. Tiempo diario estimado por dirección financiera.
    ###########################################
    def compute_r5(self, li):
        for rec in self:
            # No hay tiempos diarios para 'raw_cistern','raw_sack',
            categ_types = ['raw_pallet', 'raw_bag', 'raw_cardboard', 'raw_color']
            types = [
                #                ['raw_cistern',rec.raw_cistern_reloc_daily],
                #                ['raw_sack',rec.raw_sack_reloc_daily],
                ['raw_pallet', rec.raw_pallet_reloc_daily],
                ['raw_bag', rec.raw_bag_reloc_daily],
                ['raw_cardboard', rec.raw_cboard_reloc_daily],
                ['raw_color', rec.raw_color_reloc_daily],
            ]

            # Recorremos los tipos posibles de encontrar, con su estimacion de tiempos por tipo según la tabla anterior:
            for type in types:
                moves = self.env['stock.move'].search([
                    ('date', '>=', rec.date_from),
                    ('date', '<=', rec.date_to),
                    ('location_dest_id.usage', '=', 'production'),  # Destino es una ubicación de producción
                    ('location_id.usage', '!=', 'production'),  # Origen no es una ubicación de producción
                    ('product_id.categ_id.type', '=', type[0]),  # Tipos de familia del producto
                    ('state', '=', 'done'),  # Albarán en estado "done"
                    ('product_uom_qty', '>', 0),
                ])

                # Suma de kg total por tipo de materia prima para después hacer reparto proporcional:
                # total_weight = sum(moves.mapped('product_uom_qty')) NO HACE FALTA ESTE, SINO EL DEL POR TIPO.

                # El tiempo es estimado por tipo de producto, así que hay que recorrer por tipo:
                for type in types:
                    type_moves = self.env['stock.move'].search([
                        ('id', 'in', moves.ids),
                        ('product_id.categ_id.type', '=', type[0]),
                    ])
                    type_weight = sum(type_moves.mapped('product_uom_qty'))

                    # Recorremos por producto para hacer un único apunte R4 por cada cuenta analítica:
                    products = type_moves.product_id
                    for product in products:
                        product_moves = self.env['stock.move'].search([
                            ('id', 'in', type_moves.ids),
                            ('product_id', '=', product.id),
                        ])

                        # Reparto proporcional por si un albarán lleva varios productos [len(picking_moves)]
                        product_weight = sum(product_moves.mapped('product_uom_qty'))
                        picking_cost = (product_weight / type_weight) * li.picking_hour_cost * (type[1] * rec.days)
                        # Nombre del apunte analítico:
                        mrp_names = "[ "
                        for ref in product_moves: mrp_names += ref.reference + " "
                        mrp_names += "]"

                        # Buscamos si ya existe o se crea la cuenta analítica para este producto:
                        analytic_account = self.check_or_create_analytic_account(product)

                        # Creación del apunte analítico:
                        product_field_id = self.env.company.product_field_id.name
                        fixed_variable_field_id = self.env.company.fixed_variable_field_id.name
                        department_field_id = self.env.company.department_field_id.name
                        new_aal = self.env['account.analytic.line'].create({
                            'product_id': product.id,
                            'name': li.template_id.name + " - " + rec.name + " " + mrp_names,
                            'amount': -1 * abs(picking_cost),
                            product_field_id: analytic_account.id,
                            fixed_variable_field_id: self.env.company.analytic_variable_account_id.id,
                            department_field_id: self.env.company.analytic_warehouse_department_id.id,
                            'analytic_distribution_id': self.id,
                            'analytic_distribution_template_id': li.template_id.id,
                        })


    ###########################################
    # R6: Coste almacenamiento materia prima, por producto.
    # Sobre cuentas contables de amortizaciones. Kg mes anterior, kg fecha fin => media.
    ###########################################
    def compute_r6(self, li):
        for rec in self:
            categ_types = ['raw_cistern', 'raw_sack', 'raw_pallet', 'raw_bag', 'raw_cardboard', 'raw_color']

            total_weight_before = 0.0
            total_weight_after  = 0.0

            # Total de kg en stock de MP en fecha de inicio:
            moves_before = self.env['stock.move.line'].search([
                ('product_id.categ_id.type', 'in', categ_types),
                ('date', '<=', rec.date_from),
                ('product_id.detailed_type','=','product'),
                '|',  # Operador "OR"
                ('location_id.usage', '=', 'internal'),
                ('location_dest_id.usage', '=', 'internal'),
            ], order='date')
            for move_line in moves_before:
                # Multiplicar la cantidad por el peso del producto.
                move_weight = move_line.qty_done * move_line.product_id.weight
                # Sumar o restar el peso según la dirección del movimiento.
                if move_line.location_id.usage == 'internal':
                    total_weight_before -= move_weight
                if move_line.location_dest_id.usage == 'internal':
                    total_weight_before += move_weight

            # Total de kg en stock de MP en fecha de fin:
            moves_after = self.env['stock.move.line'].search([
                ('product_id.categ_id.type', 'in', categ_types),
                ('date', '<=', rec.date_to),
                ('product_id.detailed_type', '=', 'product'),
                '|',  # Operador "OR"
                ('location_id.usage', '=', 'internal'),
                ('location_dest_id.usage', '=', 'internal'),
            ], order='date')
            for move_line in moves_after:
                # Multiplicar la cantidad por el peso del producto.
                move_weight = move_line.qty_done * move_line.product_id.weight
                # Sumar o restar el peso según la dirección del movimiento.
                if move_line.location_id.usage == 'internal':
                    total_weight_after -= move_weight
                if move_line.location_dest_id.usage == 'internal':
                    total_weight_after += move_weight
            # Peso medio entre inicio y fin de periodo:
            stock_media_kg_cost = li.balance / (total_weight_before + total_weight_after) * 2

            # Distribución analítica proporcional:
            products_before = moves_before.product_id
            products_after = moves_after.product_id
            products = products_before + products_after
            for product in products:
                total_product_weight_before = 0
                total_product_weight_after  = 0

                product_moves_before = self.env['stock.move.line'].search([
                    ('id', 'in', moves_before.ids),
                    ('product_id', '=', product.id),
                ])
                for move_line in product_moves_before:
                    # Multiplicar la cantidad por el peso del producto.
                    move_weight = move_line.qty_done * move_line.product_id.weight
                    # Sumar o restar el peso según la dirección del movimiento.
                    if move_line.location_id.usage == 'internal':
                        total_product_weight_before -= move_weight
                    if move_line.location_dest_id.usage == 'internal':
                        total_product_weight_before += move_weight

                product_moves_after = self.env['stock.move.line'].search([
                    ('id', 'in', moves_after.ids),
                    ('product_id', '=', product.id),
                ])
                for move_line in product_moves_after:
                    # Multiplicar la cantidad por el peso del producto.
                    move_weight = move_line.qty_done * move_line.product_id.weight
                    # Sumar o restar el peso según la dirección del movimiento.
                    if move_line.location_id.usage == 'internal':
                        total_product_weight_after -= move_weight
                    if move_line.location_dest_id.usage == 'internal':
                        total_product_weight_after += move_weight

                product_stock_cost = stock_media_kg_cost * (total_product_weight_before + total_product_weight_after) / 2

                # Buscamos si ya existe o se crea la cuenta analítica para este producto:
                analytic_account = self.check_or_create_analytic_account(product)

                # Creación del apunte analítico:
                product_field_id = self.env.company.product_field_id.name
                fixed_variable_field_id = self.env.company.fixed_variable_field_id.name
                department_field_id = self.env.company.department_field_id.name
                new_aal = self.env['account.analytic.line'].create({
                    'product_id': product.id,
                    'name': li.template_id.name + " - " + rec.name,
                    'amount': -1 * abs(product_stock_cost),
                    product_field_id: analytic_account.id,
                    fixed_variable_field_id: self.env.company.analytic_variable_account_id.id,
                    department_field_id: self.env.company.analytic_warehouse_department_id.id,
                    'analytic_distribution_id': self.id,
                    'analytic_distribution_template_id': li.template_id.id,
                })

    ###########################################
    # R7: Coste almacenamiento producto FINAL.
    # Huecos por día y producto para repartir proporcionalmente (lo haremos por s/n y tipo de empaquetado).
    ###########################################

    def compute_r7(self, li):
        for rec in self:
            bom_templates = ['pallet', 'pallet_nonmrp']
            today = datetime.today()
            products_packing = self.env['product.product'].search([
                ('detailed_type', '=', 'product'),
                ('mrp_bom_template_id.type', 'in', bom_templates),
            ])

            # Cálculo del total de jornadas para poder hacer la proporción:
            total_storages  = 0
            for ppack in products_packing:
                stock_before = ppack.with_context(to_date=rec.date_from).qty_available
                current_date = rec.date_from
                while current_date <= rec.date_to and current_date <= today:
                    stock_current_date = ppack.with_context(to_date=current_date).qty_available
                    total_storages += stock_current_date
                    current_date += timedelta(days=1)

            # Cálculo por producto base pararealizar la imputación analítica:
            products = products_packing.pnt_parent_id
            for product in products:
                storages = 0
                product_packings = self.env['product.product'].search([
                    ('id','in',products_packing.ids),
                    ('pnt_parent_id','=',product.id),
                ])
                for ppacking in product_packings:
                    stock_before = ppacking.with_context(to_date=rec.date_from).qty_available
                    current_date = rec.date_from
                    while current_date <= rec.date_to and current_date <= today:
                        stock_current_date = ppacking.with_context(to_date=current_date).qty_available
                        storages += stock_current_date
                        current_date += timedelta(days=1)

                # Buscamos si ya existe o se crea la cuenta analítica para este producto:
                analytic_account = self.check_or_create_analytic_account(product)
                # Creación del apunte analítico:
                product_field_id = self.env.company.product_field_id.name
                fixed_variable_field_id = self.env.company.fixed_variable_field_id.name
                department_field_id = self.env.company.department_field_id.name
                new_aal = self.env['account.analytic.line'].create({
                    'product_id': product.id,
                    'name': li.template_id.name + " - " + rec.name,
                    'amount': -1 * abs(li.balance * storages / total_storages),
                    product_field_id: analytic_account.id,
                    fixed_variable_field_id: self.env.company.analytic_variable_account_id.id,
                    department_field_id: self.env.company.analytic_warehouse_department_id.id,
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
    purchase_estimation = fields.Float(
        string='Purchase time %',
        help='Estimated purchase % time'
    )
    purchase_estimation_handle = fields.Float(
        string='Handle purchase %',
        help='Estimated purchase % time'
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


    # =========================================================================
    # MÉTODOS DE CÁLCULO PARA DISTRIBUCIONES ANALÍTICAS:
    # =========================================================================

    """

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
