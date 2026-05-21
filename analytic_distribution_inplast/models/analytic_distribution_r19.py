# -*- coding: utf-8 -*-
# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
#
# R19: Distribución de costes entre productos base por palets servidos a cliente.
#
# Objetivo:
#   Repartir el balance entre los productos base (tapones) proporcionalmente al
#   número de palets de producto packing entregados a cliente en el periodo,
#   obtenidos de los movimientos de stock en albaranes de salida (done).
#
# ─── FUENTE DE DATOS ──────────────────────────────────────────────────────────
#   stock.move de albaranes outgoing (estado done) del periodo, con productos
#   de tipo packing. El número de palets de cada movimiento se calcula como:
#
#     palets_movimiento = product_uom_qty / bom.pallet_line_id.product_qty
#
#   donde bom es la lista de materiales del producto packing y
#   pallet_line_id.product_qty es la cantidad de unidades por palet.
#
#   Si un packing no tiene BoM o su BoM no tiene pallet_line_id configurado,
#   se avisa por log y se ignora.
#
# ─── REPARTO ──────────────────────────────────────────────────────────────────
#   Los palets se acumulan por producto base (packing.pnt_parent_id).
#   El coste de cada producto base es proporcional a su número de palets:
#
#     coste_base = balance × (palets_base / palets_total)
from odoo import models
import logging

_logger = logging.getLogger(__name__)


class AnalyticDistribution(models.Model):
    _inherit = 'analytic.distribution'

    def compute_r19(self, li):
        """Distribuye li.balance entre productos base proporcionalmente al número
        de palets de packing servidos a cliente en el periodo.

        Parámetros:
            li  (analytic.distribution.line): línea con el template R19 que
                contiene el balance contable a distribuir.
        """
        for rec in self:
            method = 'R19'
            balance = li.balance
            _logger.warning("[%s] Iniciando cálculo. balance=%.2f", method, balance)
            if not balance:
                _logger.warning("[%s] SALIDA: balance es 0 o nulo.", method)
                return

            date_from = rec.date_from
            date_to = rec.date_to
            _logger.warning("[%s] Periodo: %s → %s", method, date_from, date_to)

            # ------------------------------------------------------------------
            # 1. Movimientos de salida a cliente del periodo, productos packing.
            # ------------------------------------------------------------------
            moves = self.env['stock.move'].search([
                ('picking_id.picking_type_code', '=', 'outgoing'),
                ('picking_id.state', '=', 'done'),
                ('picking_id.date_done', '>=', date_from),
                ('picking_id.date_done', '<=', date_to),
                ('product_id.pnt_product_type', '=', 'packing'),
                ('product_uom_qty', '>', 0),
            ])
            _logger.warning("[%s] Movimientos packing outgoing encontrados: %d", method, len(moves))
            if not moves:
                _logger.warning("[%s] SALIDA: no hay movimientos en el periodo.", method)
                return

            # ------------------------------------------------------------------
            # 2. Acumular palets por producto base.
            # ------------------------------------------------------------------
            pallets_per_base = {}

            for move in moves:
                packing = move.product_id
                base_tmpl = packing.pnt_parent_id
                if not base_tmpl:
                    _logger.warning(
                        "[%s]   Packing '%s' sin pnt_parent_id, ignorado.", method, packing.name
                    )
                    continue

                # Obtener BoM del packing para leer pallet_line_id.product_qty
                bom = self.env['mrp.bom'].search([
                    ('product_tmpl_id', '=', packing.product_tmpl_id.id),
                ], limit=1)
                if not bom:
                    bom = self.env['mrp.bom'].search([
                        ('product_tmpl_id', '=', packing.product_tmpl_id.id),
                        ('type', '!=', 'phantom'),
                    ], limit=1)

                if not bom or not bom.pallet_line_id or not bom.pallet_line_id.product_qty:
                    _logger.warning(
                        "[%s]   Packing '%s' sin BoM o sin pallet_line_id.product_qty, ignorado.",
                        method, packing.name
                    )
                    continue

                units_per_pallet = bom.pallet_line_id.product_qty
                pallets = move.product_uom_qty / units_per_pallet
                pallets_per_base[base_tmpl] = pallets_per_base.get(base_tmpl, 0.0) + pallets

                _logger.warning(
                    "[%s]   '%s' → base='%s' | qty=%.2f / %s u/palet = %.4f palets",
                    method, packing.name, base_tmpl.name,
                    move.product_uom_qty, units_per_pallet, pallets
                )

            total_pallets = sum(pallets_per_base.values())
            _logger.warning("[%s] Total palets acumulados: %.4f | Productos base: %d",
                            method, total_pallets, len(pallets_per_base))

            if total_pallets <= 0:
                _logger.warning("[%s] SALIDA: total palets = 0.", method)
                return

            # ------------------------------------------------------------------
            # 3. Campos analíticos comunes.
            # ------------------------------------------------------------------
            product_field_id = self.env.company.product_field_id.name
            fixed_variable_field_id = self.env.company.fixed_variable_field_id.name
            department_field_id = self.env.company.department_field_id.name
            warehouse_dept = self.env.company.analytic_warehouse_department_id
            variable_account = self.env.company.analytic_variable_account_id

            # ------------------------------------------------------------------
            # 4. Crear apuntes analíticos proporcionales a los palets.
            # ------------------------------------------------------------------
            for base_tmpl, pallets in pallets_per_base.items():
                proportion = pallets / total_pallets
                cost = balance * proportion
                proportion_pct = proportion * 100

                base_product = base_tmpl.product_variant_ids[:1]
                analytic_account = self.check_or_create_analytic_account(base_tmpl)

                note = (
                    f"Informe: {method} — Palets servidos a cliente\n"
                    f"Producto base: {base_tmpl.name}\n"
                    f"─── Reparto ───\n"
                    f"  Balance: {balance:.2f}\n"
                    f"  Palets producto: {pallets:.4f}\n"
                    f"  Palets total:    {total_pallets:.4f}\n"
                    f"  Proporción: {proportion_pct:.4f}%\n"
                    f"  Coste asignado = {balance:.2f} × {proportion_pct:.4f}% = {cost:.2f}"
                )

                self.env['account.analytic.line'].create({
                    'product_id': base_product.id if base_product else False,
                    'name': f"{li.template_id.name} - {rec.name} | {base_tmpl.name}",
                    'amount': -abs(cost),
                    'date': rec.date_to,
                    product_field_id: analytic_account.id,
                    fixed_variable_field_id: variable_account.id if variable_account else False,
                    'analytic_distribution_id': rec.id,
                    'analytic_distribution_template_id': li.template_id.id,
                    'analytic_distribution_note': note,
                })
                _logger.warning("[%s]   Apunte creado: %s → %.4f palets (%.4f%%) → %.2f€",
                                method, base_tmpl.name, pallets, proportion_pct, cost)
