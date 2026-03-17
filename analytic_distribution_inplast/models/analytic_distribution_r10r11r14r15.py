# -*- coding: utf-8 -*-
# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
#
# R10 / R11 / R14 / R15: Distribución de costes de máquina entre productos fabricados.
#
# Los cuatro informes comparten el mismo algoritmo; la única diferencia es el
# balance a distribuir, que proviene de cuentas contables distintas
# configuradas en cada plantilla.
#
# Objetivo:
#   Repartir el coste total del periodo (li.balance) entre los productos
#   fabricados en los centros de trabajo declarados en la plantilla,
#   proporcionalmente a las horas reales de máquina empleadas.
#
# Fuente del coste:
#   li.balance  →  saldo de las cuentas contables de la plantilla.
#
# Base de reparto:
#   Para cada orden de trabajo (mrp.workorder) ejecutada en los centros de
#   trabajo configurados en la plantilla durante el periodo:
#       horas_producto = Σ duration (minutos) / 60
#   precio_hora = balance / horas_totales
#   coste_producto = horas_producto × precio_hora
#
# Salida:
#   Un apunte analítico (account.analytic.line) por cada producto fabricado,
#   con el coste que le corresponde según sus horas de máquina.
#   Si el producto fabricado es de tipo 'packing', el apunte se imputa a la
#   cuenta analítica del producto final padre (pnt_parent_id).
#
# Nota:
#   La única diferencia con R13 es que R13 pondera por duration × power_kw
#   (kWh), mientras que R10/R11 ponderan solo por duration (horas puras),
#   ya que el coste que se reparte no es electricidad sino otro concepto
#   de máquina.
from odoo import fields, models
import logging
_logger = logging.getLogger(__name__)


class AnalyticDistribution(models.Model):
    _inherit = 'analytic.distribution'

    def compute_r10r11(self, li):
        """Distribuye li.balance entre los productos fabricados en los centros
        de trabajo de la plantilla, proporcionalmente a las horas reales de
        máquina consumidas.

        Válido para R10 y R11. La diferencia entre ambos es únicamente el
        balance a repartir (cuentas contables distintas en cada plantilla).

        Parámetros:
            li  (analytic.distribution.line): línea con el template R10 o R11
                que contiene el balance contable a distribuir y los centros de
                trabajo (workcenter_ids) sobre los que actuar.
        """
        for rec in self:
            method = li.template_id.compute_method.upper()
            balance = li.balance
            _logger.warning("[%s] Iniciando cálculo. balance=%.2f", method, balance)
            if not balance:
                _logger.warning("[%s] SALIDA: balance es 0 o nulo.", method)
                return

            date_from = rec.date_from
            date_to = rec.date_to
            workcenters = li.template_id.workcenter_ids
            _logger.warning("[%s] Periodo: %s → %s | Centros de trabajo: %d",
                            method, date_from, date_to, len(workcenters))

            if not workcenters:
                _logger.warning("[%s] SALIDA: no hay centros de trabajo configurados en la plantilla.", method)
                return

            # ------------------------------------------------------------------
            # 1. Órdenes de trabajo ejecutadas en los centros de trabajo
            #    de la plantilla durante el periodo.
            # ------------------------------------------------------------------
            workorders = self.env['mrp.workorder'].search([
                ('workcenter_id', 'in', workcenters.ids),
                ('date_start', '>=', date_from),
                ('date_start', '<=', date_to),
                ('state', '=', 'done'),
            ])
            _logger.warning("[%s] Órdenes de trabajo encontradas: %d", method, len(workorders))
            if not workorders:
                _logger.warning("[%s] SALIDA: no hay órdenes de trabajo en el periodo.", method)
                return

            # ------------------------------------------------------------------
            # 2. Acumulación de horas por producto fabricado.
            #    product_hours: { product.product: minutos_totales }
            # ------------------------------------------------------------------
            product_hours = {}
            product_workcenter_details = {}  # para la nota descriptiva

            for wo in workorders:
                product = wo.product_id
                duration = wo.duration  # minutos
                workcenter = wo.workcenter_id

                product_hours[product] = product_hours.get(product, 0.0) + duration

                details = product_workcenter_details.setdefault(product, {})
                if workcenter not in details:
                    details[workcenter] = 0.0
                details[workcenter] += duration

            total_minutes = sum(product_hours.values())
            total_hours = total_minutes / 60.0
            _logger.warning("[%s] Total horas: %.2f | Productos distintos: %d",
                            method, total_hours, len(product_hours))

            if total_hours <= 0:
                _logger.warning("[%s] SALIDA: total de horas es 0.", method)
                return

            price_per_hour = balance / total_hours
            _logger.warning("[%s] Precio/hora: %.4f €/h", method, price_per_hour)

            # ------------------------------------------------------------------
            # 3. Creación de apuntes analíticos: uno por producto fabricado.
            # ------------------------------------------------------------------
            product_field_id = self.env.company.product_field_id.name
            fixed_variable_field_id = self.env.company.fixed_variable_field_id.name
            department_field_id = self.env.company.department_field_id.name
            mrp_dept = self.env.company.analytic_mrp_department_id
            variable_account = self.env.company.analytic_variable_account_id

            for product, minutes in product_hours.items():
                hours = minutes / 60.0
                proportion = hours / total_hours
                cost = balance * proportion
                proportion_pct = proportion * 100

                # Si es packing, imputar al producto final padre
                analytic_product = product
                if product.pnt_product_type == 'packing':
                    analytic_product = product.pnt_parent_id

                # Desglose por centro de trabajo para la nota
                wc_lines = "\n".join(
                    f"  · {wc.name}: {mins:.1f} min ({mins / 60:.2f} h)"
                    for wc, mins in product_workcenter_details[product].items()
                )
                note = (
                    f"Informe: {method}\n"
                    f"Producto: {product.name}\n"
                    f"─── Horas por centro de trabajo ───\n"
                    f"{wc_lines}\n"
                    f"─── Totales ───\n"
                    f"Horas producto: {hours:.2f} h / {total_hours:.2f} h total\n"
                    f"Proporción: {proportion_pct:.4f}%\n"
                    f"Precio/hora: {price_per_hour:.4f} €/h\n"
                    f"Balance a repartir: {balance:.2f}\n"
                    f"Coste asignado = {balance:.2f} × {proportion_pct:.4f}% = {cost:.2f}"
                )

                analytic_account = self.check_or_create_analytic_account(analytic_product)
                self.env['account.analytic.line'].create({
                    'product_id': product.id,
                    'name': f"{li.template_id.name} - {rec.name} | {product.name}",
                    'amount': -abs(cost),
                    product_field_id: analytic_account.id,
                    fixed_variable_field_id: variable_account.id,
                    'analytic_distribution_id': rec.id,
                    'analytic_distribution_template_id': li.template_id.id,
                    'analytic_distribution_note': note,
                })
                _logger.warning("[%s]   Apunte creado: %s | %.2f h → %.2f€ (%.4f%%)",
                                method, product.name, hours, cost, proportion_pct)
