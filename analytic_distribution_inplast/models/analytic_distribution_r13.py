# -*- coding: utf-8 -*-
# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
#
# R13: Distribución del coste de electricidad entre productos fabricados.
#
# Objetivo:
#   Repartir el coste total de las facturas de electricidad del periodo
#   (obtenido de `li.balance`, calculado por `compute_debit_credit()` a partir
#   de las cuentas contables configuradas en la plantilla) entre los productos
#   fabricados en los centros de trabajo declarados, de forma proporcional al
#   consumo eléctrico real de cada máquina.
#
# Fuente del coste:
#   li.balance  →  saldo de las cuentas de electricidad (facturas contabilizadas
#                  en el periodo para los analíticos de la plantilla R13).
#
# Base de reparto:
#   Para cada orden de trabajo (mrp.workorder) ejecutada en los centros de
#   trabajo configurados en la plantilla:
#       kWh_consumidos = duration_minutos * power_kw
#   La proporción de cada producto = sus kWh / kWh totales de todas las máquinas.
#
# Nota sobre unidades:
#   `mrp.workorder.duration` está en minutos y `mrp.workcenter.power_kw` es la
#   potencia en kW. La multiplicación directa (minutos × kW) da una magnitud
#   proporcional al consumo real; para obtener kWh exactos habría que dividir
#   entre 60, pero al ser un reparto proporcional el factor constante se cancela.
#
# Salida:
#   Un apunte analítico (account.analytic.line) por cada producto fabricado,
#   con el coste de electricidad que le corresponde según su consumo eléctrico.
#   Si el producto fabricado es de tipo 'packing', el apunte se imputa a la
#   cuenta analítica del producto final padre (pnt_parent_id).
from odoo import fields, models, api
from odoo.exceptions import UserError


class AnalyticDistribution(models.Model):
    _inherit = 'analytic.distribution'

    def compute_r13(self, li):
        """Distribuye el coste de electricidad (li.balance) entre los productos
        fabricados en los centros de trabajo de la plantilla, proporcionalmente
        al consumo eléctrico declarado (duration × power_kw) de cada máquina.

        Parámetros:
            li  (analytic.distribution.line): línea con el template R13 que
                contiene el balance contable a distribuir y los centros de
                trabajo (workcenter_ids) sobre los que actuar.
        """
        datefrom = self.date_from
        dateto = self.date_to
        total_kwh = 0  # Acumulador del consumo total de todas las máquinas (en unidades proporcionales min×kW)
        workcenters = li.template_id.workcenter_ids  # Centros de trabajo incluidos en esta plantilla R13
        balance = li.balance  # Coste total de electricidad a distribuir (€), calculado por compute_debit_credit()

        # Órdenes de trabajo ejecutadas en los centros de trabajo del template durante el periodo.
        # Se filtra por date_start para capturar las órdenes iniciadas en el mes.
        workorders = self.env["mrp.workorder"].search(
            [
                ("workcenter_id", "in", workcenters.ids),
                ("date_start", ">=", datefrom),
                ("date_start", "<=", dateto),
            ]
        )

        # Listas paralelas para acumular kWh por producto fabricado.
        # mrpproducts[i] ↔ product_total_kwh[i] ↔ product_machine_details[i]
        mrpproducts = []
        product_total_kwh = []
        # Desglose por máquina para cada producto: lista de dicts con los datos
        # de cada orden de trabajo, usado posteriormente en analytic_distribution_note.
        product_machine_details = []

        # Recorremos cada orden de trabajo para calcular el consumo eléctrico acumulado por producto.
        for wo in workorders:
            product = wo.product_id       # Producto fabricado en esta orden
            duration = wo.duration        # Duración de la orden en minutos
            machine = wo.workcenter_id    # Centro de trabajo (máquina) con su potencia declarada en power_kw

            # Añadimos el producto a la lista si es la primera vez que aparece
            if product not in mrpproducts:
                mrpproducts.append(product)
                product_total_kwh.append(0)  # Inicializamos su acumulador de consumo a 0
                product_machine_details.append([])  # Lista vacía de detalles por máquina

            # Consumo proporcional de esta orden: duración (min) × potencia (kW)
            # (factor constante 1/60 se omite al ser un reparto proporcional)
            kwh_consumed = duration * machine.power_kw
            total_kwh += kwh_consumed

            # Acumulamos el consumo al producto correspondiente
            product_index = mrpproducts.index(product)
            product_total_kwh[product_index] += kwh_consumed

            # Guardamos el detalle de esta orden para la nota descriptiva
            product_machine_details[product_index].append({
                'machine': machine.name,
                'power_kw': machine.power_kw,
                'duration_min': duration,
                'kwh': kwh_consumed,
            })

        # Protección frente a división por cero: si no hay consumo registrado no
        # es posible repartir el coste de electricidad.
        if total_kwh == 0:
            raise UserError("No hay consumo de energía registrado.")

        # Creación de apuntes analíticos: uno por cada producto fabricado en el periodo.
        for i in range(len(mrpproducts)):
            product = mrpproducts[i]
            product_kwh = product_total_kwh[i]

            # Proporción del consumo de este producto sobre el total (%)
            machine_percentage = (product_kwh / total_kwh) * 100
            # Coste de electricidad asignado a este producto
            machine_cost = (balance * machine_percentage) / 100

            # Nota descriptiva con el desglose del cálculo por máquina
            details = product_machine_details[i]
            # Agrupamos los detalles por máquina para evitar repetir su nombre
            machine_summary = {}
            for d in details:
                key = d['machine']
                if key not in machine_summary:
                    machine_summary[key] = {'power_kw': d['power_kw'], 'duration_min': 0.0, 'kwh': 0.0}
                machine_summary[key]['duration_min'] += d['duration_min']
                machine_summary[key]['kwh'] += d['kwh']

            machine_lines = "\n".join(
                f"  · {name}: {v['power_kw']:.2f} kW × {v['duration_min']:.1f} min = {v['kwh']:.2f} u.prop."
                for name, v in machine_summary.items()
            )
            note = (
                f"Producto: {product.name}\n"
                f"Coste total electricidad (balance): {balance:.2f}\n"
                f"─── Desglose por máquina ───\n"
                f"{machine_lines}\n"
                f"─── Totales ───\n"
                f"Consumo producto (u.prop.): {product_kwh:.2f} / {total_kwh:.2f} total\n"
                f"Porcentaje: {machine_percentage:.2f}%\n"
                f"Coste asignado = {balance:.2f} × {machine_percentage:.2f}% = {machine_cost:.2f}"
            )

            # Si el producto es un packing, el apunte se imputa al producto final
            # padre (pnt_parent_id), que es el que tiene cuenta analítica propia.
            analytic_product = product
            if product.pnt_product_type == 'packing':
                analytic_product = product.pnt_parent_id

            # Buscar la cuenta analítica del producto o crearla si no existe.
            # Se usa el helper estándar del módulo, que busca por nombre y plan
            # configurado en la compañía (analytic_product_plan_id).
            analytic_account = self.check_or_create_analytic_account(analytic_product)

            # Nombre del campo dinámico del plan analítico en account.analytic.line,
            # obtenido desde la configuración de compañía (mismo patrón que R1-R8).
            product_field_id = self.env.company.product_field_id.name
            department_field_id = self.env.company.department_field_id.name
            mrp_dept = self.env.company.analytic_mrp_department_id

            self.env["account.analytic.line"].create(
                {
                    "name": f"Consumo {product.name}",
                    "amount": machine_cost,
                    "product_id": product.id,
                    "date": self.date_to,
                    "analytic_distribution_id": self.id,
                    "analytic_distribution_template_id": li.template_id.id,
                    product_field_id: analytic_account.id,
                    "analytic_distribution_note": note,
                }
            )

        return True

    # =========================================================================
    # R13 LEGACY: misma lógica pero usando mrp.production.legacy
    # =========================================================================
    #
    # mrp.production.legacy expone:
    #   name         → product.template (packing fabricado)
    #   parent_id    → product.template base (related: name.pnt_parent_id)
    #   product_qty  → unidades fabricadas
    #   date         → fecha (Date)
    #   machine_id   → account.analytic.account (máquina/workcenter)
    #   time         → horas empleadas (Float) — ya en horas, no en minutos
    #
    # kWh = time (h) × power_kw (kW) → resultado directo en kWh
    #
    # Enlace account.analytic.account → mrp.workcenter:
    #   account.analytic.account.workcenter_id → mrp.workcenter
    #   (unique constraint garantiza relación 1:1)
    # =========================================================================

    def compute_r13_legacy(self, li):
        """Versión legacy de compute_r13: usa mrp.production.legacy en lugar de
        mrp.workorder para distribuir el coste de electricidad entre los
        productos fabricados, proporcionalmente al consumo eléctrico real
        (horas × potencia kW) de cada máquina.

        Parámetros:
            li  (analytic.distribution.line): línea con el template R13_LEGACY
                que contiene el balance a distribuir y los workcenters (workcenter_ids).
        """
        date_from = self.date_from
        date_to = self.date_to
        date_from_d = date_from.date() if hasattr(date_from, 'date') else date_from
        date_to_d = date_to.date() if hasattr(date_to, 'date') else date_to

        workcenters = li.template_id.workcenter_ids
        balance = li.balance

        # Obtener las cuentas analíticas correspondientes a los workcenters del template
        analytic_accts = self.env['account.analytic.account'].search([
            ('workcenter_id', 'in', workcenters.ids),
        ])

        # Registros legacy del periodo para las máquinas del template
        legacy_records = self.env['mrp.production.legacy'].search([
            ('machine_id', 'in', analytic_accts.ids),
            ('date', '>=', date_from_d),
            ('date', '<=', date_to_d),
        ])

        # Listas paralelas para acumular kWh por producto base fabricado.
        # base_products[i] ↔ product_total_kwh[i] ↔ product_machine_details[i]
        base_products = []
        product_total_kwh = []
        product_machine_details = []
        total_kwh = 0.0

        for lr in legacy_records:
            workcenter = lr.machine_id.workcenter_id
            if not workcenter:
                continue

            # time está en horas → kWh = horas × kW
            kwh_consumed = lr.time * workcenter.power_kw
            total_kwh += kwh_consumed

            # Producto base: parent_id si existe, si no el packing mismo
            base_tmpl = lr.parent_id or lr.name
            if not base_tmpl:
                continue

            if base_tmpl not in base_products:
                base_products.append(base_tmpl)
                product_total_kwh.append(0.0)
                product_machine_details.append([])

            idx = base_products.index(base_tmpl)
            product_total_kwh[idx] += kwh_consumed
            product_machine_details[idx].append({
                'machine': workcenter.name,
                'power_kw': workcenter.power_kw,
                'duration_h': lr.time,
                'kwh': kwh_consumed,
                'packing': lr.name.name,
            })

        if total_kwh == 0:
            raise UserError("No hay consumo de energía registrado en producción legacy para el periodo.")

        product_field_id = self.env.company.product_field_id.name

        for i in range(len(base_products)):
            base_tmpl = base_products[i]
            product_kwh = product_total_kwh[i]

            machine_percentage = (product_kwh / total_kwh) * 100
            machine_cost = (balance * machine_percentage) / 100

            # Desglose por máquina agrupado para la nota
            details = product_machine_details[i]
            machine_summary = {}
            for d in details:
                key = d['machine']
                if key not in machine_summary:
                    machine_summary[key] = {'power_kw': d['power_kw'], 'duration_h': 0.0, 'kwh': 0.0}
                machine_summary[key]['duration_h'] += d['duration_h']
                machine_summary[key]['kwh'] += d['kwh']

            machine_lines = "\n".join(
                f"  · {name}: {v['power_kw']:.2f} kW × {v['duration_h']:.2f} h = {v['kwh']:.2f} kWh"
                for name, v in machine_summary.items()
            )
            note = (
                f"Informe: R13_LEGACY — Electricidad (Legacy)\n"
                f"Producto base: {base_tmpl.name}\n"
                f"Coste total electricidad (balance): {balance:.2f}\n"
                f"─── Desglose por máquina ───\n"
                f"{machine_lines}\n"
                f"─── Totales ───\n"
                f"Consumo producto (kWh): {product_kwh:.2f} / {total_kwh:.2f} total\n"
                f"Porcentaje: {machine_percentage:.2f}%\n"
                f"Coste asignado = {balance:.2f} × {machine_percentage:.2f}% = {machine_cost:.2f}"
            )

            analytic_account = self.check_or_create_analytic_account(base_tmpl)
            product_pp = base_tmpl.product_variant_ids[:1]

            self.env["account.analytic.line"].create({
                "name": f"Consumo electricidad {base_tmpl.name}",
                "amount": machine_cost,
                "product_id": product_pp.id if product_pp else False,
                "date": self.date_to,
                "analytic_distribution_id": self.id,
                "analytic_distribution_template_id": li.template_id.id,
                product_field_id: analytic_account.id,
                "analytic_distribution_note": note,
            })

        return True
