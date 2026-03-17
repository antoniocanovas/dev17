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

    # =========================================================================
    # R10 / R11 / R14 / R15 LEGACY: misma lógica pero usando mrp.production.legacy
    # =========================================================================
    #
    # mrp.production.legacy expone:
    #   name         → product.template (packing fabricado)
    #   parent_id    → product.template base (related: name.pnt_parent_id)
    #   date         → fecha (Date)
    #   machine_id   → account.analytic.account (máquina/workcenter)
    #   time         → horas empleadas (Float) — ya en horas, no en minutos
    #
    # Enlace: account.analytic.account.workcenter_id → mrp.workcenter
    # Filtro por workcenters del template: buscar cuentas analíticas con
    #   workcenter_id in template.workcenter_ids, luego legacy por machine_id.
    # =========================================================================

    def compute_r10r11_legacy(self, li):
        """Versión legacy de compute_r10r11: usa mrp.production.legacy en lugar
        de mrp.workorder para distribuir li.balance entre los productos
        fabricados, proporcionalmente a las horas reales de máquina empleadas.

        Válido para R10_LEGACY, R11_LEGACY, R14_LEGACY y R15_LEGACY.
        La diferencia entre ellos es únicamente el balance a repartir
        (cuentas contables distintas en cada plantilla).

        Parámetros:
            li  (analytic.distribution.line): línea con el template legacy que
                contiene el balance contable a distribuir y los centros de
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
            date_from_d = date_from.date() if hasattr(date_from, 'date') else date_from
            date_to_d = date_to.date() if hasattr(date_to, 'date') else date_to
            workcenters = li.template_id.workcenter_ids
            _logger.warning("[%s] Periodo: %s → %s | Centros de trabajo: %d",
                            method, date_from_d, date_to_d, len(workcenters))

            if not workcenters:
                _logger.warning("[%s] SALIDA: no hay centros de trabajo configurados en la plantilla.", method)
                return

            # ------------------------------------------------------------------
            # 1. Cuentas analíticas de los workcenters del template y registros
            #    legacy del periodo para esas máquinas.
            # ------------------------------------------------------------------
            analytic_accts = self.env['account.analytic.account'].search([
                ('workcenter_id', 'in', workcenters.ids),
            ])
            legacy_records = self.env['mrp.production.legacy'].search([
                ('machine_id', 'in', analytic_accts.ids),
                ('date', '>=', date_from_d),
                ('date', '<=', date_to_d),
            ])
            _logger.warning("[%s] Registros legacy encontrados: %d", method, len(legacy_records))
            if not legacy_records:
                _logger.warning("[%s] SALIDA: no hay registros legacy en el periodo.", method)
                return

            # ------------------------------------------------------------------
            # 2. Acumulación de horas por producto base.
            #    product_hours: { product.template: horas_totales }
            #    time ya está en horas → no hay que dividir entre 60.
            # ------------------------------------------------------------------
            product_hours = {}
            product_workcenter_details = {}  # para la nota descriptiva

            for lr in legacy_records:
                workcenter = lr.machine_id.workcenter_id
                base_tmpl = lr.parent_id or lr.name
                if not base_tmpl:
                    continue

                product_hours[base_tmpl] = product_hours.get(base_tmpl, 0.0) + lr.time

                details = product_workcenter_details.setdefault(base_tmpl, {})
                wc_key = workcenter if workcenter else lr.machine_id
                details[wc_key] = details.get(wc_key, 0.0) + lr.time

            total_hours = sum(product_hours.values())
            _logger.warning("[%s] Total horas: %.2f | Productos distintos: %d",
                            method, total_hours, len(product_hours))

            if total_hours <= 0:
                _logger.warning("[%s] SALIDA: total de horas es 0.", method)
                return

            price_per_hour = balance / total_hours
            _logger.warning("[%s] Precio/hora: %.4f €/h", method, price_per_hour)

            # ------------------------------------------------------------------
            # 3. Creación de apuntes analíticos: uno por producto base.
            # ------------------------------------------------------------------
            product_field_id = self.env.company.product_field_id.name
            fixed_variable_field_id = self.env.company.fixed_variable_field_id.name
            variable_account = self.env.company.analytic_variable_account_id

            for base_tmpl, hours in product_hours.items():
                proportion = hours / total_hours
                cost = balance * proportion
                proportion_pct = proportion * 100

                wc_lines = "\n".join(
                    f"  · {wc.name if hasattr(wc, 'name') else wc}: {h:.2f} h"
                    for wc, h in product_workcenter_details[base_tmpl].items()
                )
                note = (
                    f"Informe: {method} (Legacy)\n"
                    f"Producto base: {base_tmpl.name}\n"
                    f"─── Horas por centro de trabajo ───\n"
                    f"{wc_lines}\n"
                    f"─── Totales ───\n"
                    f"Horas producto: {hours:.2f} h / {total_hours:.2f} h total\n"
                    f"Proporción: {proportion_pct:.4f}%\n"
                    f"Precio/hora: {price_per_hour:.4f} €/h\n"
                    f"Balance a repartir: {balance:.2f}\n"
                    f"Coste asignado = {balance:.2f} × {proportion_pct:.4f}% = {cost:.2f}"
                )

                analytic_account = self.check_or_create_analytic_account(base_tmpl)
                product_pp = base_tmpl.product_variant_ids[:1]
                self.env['account.analytic.line'].create({
                    'product_id': product_pp.id if product_pp else False,
                    'name': f"{li.template_id.name} - {rec.name} | {base_tmpl.name}",
                    'amount': -abs(cost),
                    product_field_id: analytic_account.id,
                    fixed_variable_field_id: variable_account.id,
                    'analytic_distribution_id': rec.id,
                    'analytic_distribution_template_id': li.template_id.id,
                    'analytic_distribution_note': note,
                })
                _logger.warning("[%s]   Apunte creado: %s | %.2f h → %.2f€ (%.4f%%)",
                                method, base_tmpl.name, hours, cost, proportion_pct)
