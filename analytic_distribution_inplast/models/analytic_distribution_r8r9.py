# -*- coding: utf-8 -*-
# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
#
# R8 / R9: Distribución del coste de componentes de fabricación.
#
# Ambos informes comparten el mismo algoritmo; la única diferencia es el tipo
# de componente sobre el que actúan:
#
#   R8 → Materias primas:  pnt_product_type in ['raw', 'dye', 'additive']
#   R9 → Embalajes:        pnt_product_type in ['packaging', 'box', 'pallet']
#
# Objetivo:
#   Repartir el coste total del periodo (obtenido de `li.balance`, calculado
#   por `compute_debit_credit()` a partir de las cuentas contables configuradas
#   en la plantilla) entre los productos finales fabricados, de forma
#   proporcional al coste teórico del componente que corresponde a cada uno
#   según su BoM.
#
# Fuente del coste:
#   li.balance  →  saldo de las cuentas contables de la plantilla
#                  (60x MP para R8, 60x embalajes para R9).
#
# Clave de reparto:
#   Para cada par (componente, PF):
#       peso = consumo_teórico(componente, PF) × standard_price(componente)
#   donde consumo_teórico se obtiene explotando recursivamente la BoM de
#   cada PF, escalada por la producción real del periodo (calculada a partir
#   de los movimientos de los productos packing asociados).
#
#   La proporción de cada par = peso / peso_total_todos_los_pares.
#
# Salida:
#   Un apunte analítico (account.analytic.line) por cada par (componente, PF),
#   con el coste = li.balance × proporción.
#   La suma de todos los apuntes coincide exactamente con li.balance.
from odoo import fields, models, api
import logging
_logger = logging.getLogger(__name__)


class AnalyticDistribution(models.Model):
    _inherit = 'analytic.distribution'

    # =========================================================================
    # R8 / R9: Distribución del coste de componentes entre productos fabricados.
    # =========================================================================

    def compute_r8r9(self, li):
        """Distribuye li.balance entre los productos finales fabricados en el
        periodo, proporcionalmente al coste teórico de componentes de cada uno
        según la explosión de su BoM valorada a precio de coste (standard_price).

        Válido para R8 (materias primas) y R9 (embalajes). El tipo de componente
        se determina automáticamente a partir de li.template_id.compute_method.

        Parámetros:
            li  (analytic.distribution.line): línea con el template R8 o R9 que
                contiene el balance contable a distribuir.
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
            _logger.warning("[%s] Periodo: %s → %s", method, date_from, date_to)

            # ------------------------------------------------------------------
            # 1. Identificación de componentes según el método R8 o R9
            # ------------------------------------------------------------------
            if li.template_id.compute_method == 'r8':
                component_types = ['raw', 'dye', 'additive']
            else:  # r9
                component_types = ['packaging', 'box', 'pallet']

            raw_materials = self.env['product.product'].search([
                ('pnt_product_type', 'in', component_types)
            ])
            raw_material_ids = set(raw_materials.ids)
            _logger.warning("[%s] Tipos de componente: %s → %d productos encontrados",
                            method, component_types, len(raw_materials))

            final_products = self.env['product.product'].search([
                ('pnt_product_type', '=', 'final'),
                ('categ_id.type', '=', 'cap_mrp'),
            ])
            _logger.warning("[%s] Productos finales (PF): %d", method, len(final_products))
            if not final_products:
                _logger.warning("[%s] SALIDA: no hay productos finales.", method)
                return

            # ------------------------------------------------------------------
            # 2. Producción real de PF via movimientos de packings.
            #    Cada packing contiene pnt_parent_qty unidades del PF padre.
            #    qty_fabricada_PF = Σ_packings (variación_stock × pnt_parent_qty)
            # ------------------------------------------------------------------
            packing_products = self.env['product.product'].search([
                ('pnt_parent_id', 'in', final_products.ids),
                ('pnt_parent_qty', '>', 0),
            ])
            _logger.warning("[%s] Packings encontrados: %d", method, len(packing_products))

            packing_out = {
                g['product_id'][0]: g['product_uom_qty']
                for g in self.env['stock.move'].read_group(
                    [
                        ('product_id', 'in', packing_products.ids),
                        ('date', '>=', date_from),
                        ('date', '<=', date_to),
                        ('picking_type_id.code', '=', 'outgoing'),
                        ('state', '=', 'done'),
                    ],
                    ['product_id', 'product_uom_qty:sum'],
                    ['product_id'],
                )
            }
            packing_in = {
                g['product_id'][0]: g['product_uom_qty']
                for g in self.env['stock.move'].read_group(
                    [
                        ('product_id', 'in', packing_products.ids),
                        ('date', '>=', date_from),
                        ('date', '<=', date_to),
                        ('picking_type_id.code', '=', 'incoming'),
                        ('state', '=', 'done'),
                    ],
                    ['product_id', 'product_uom_qty:sum'],
                    ['product_id'],
                )
            }

            # produced_pf: {product.template (PF): qty_fabricada}
            produced_pf = {}
            for packing in packing_products:
                sf = packing.with_context(to_date=date_to).qty_available
                si = packing.with_context(to_date=date_from).qty_available
                sales = packing_out.get(packing.id, 0.0)
                purchases = packing_in.get(packing.id, 0.0)

                qty_produced = (sf - si + sales - purchases) * packing.pnt_parent_qty
                _logger.warning("[%s]   Packing '%s': si=%.2f sf=%.2f sales=%.2f purch=%.2f → qty_produced=%.2f",
                                method, packing.name, si, sf, sales, purchases, qty_produced)
                if qty_produced > 0:
                    pf = packing.pnt_parent_id
                    produced_pf[pf] = produced_pf.get(pf, 0.0) + qty_produced

            _logger.warning("[%s] PF con producción > 0: %d → %s",
                            method, len(produced_pf),
                            [(pf.name, round(q, 2)) for pf, q in produced_pf.items()])
            if not produced_pf:
                _logger.warning("[%s] SALIDA: ningún PF con producción positiva en el periodo.", method)
                return

            # ------------------------------------------------------------------
            # 3. Consumo teórico por PF fabricado.
            #
            #   R8: explosión recursiva de la BoM del producto final
            #       → hojas raw / dye / additive
            #
            #   R9: lectura directa de las líneas de la BoM de cada packing
            #       (que contiene los embalajes físicos).  Los embalajes nunca
            #       tienen sub-BoM, por lo que no es necesaria la recursión.
            #       qty_packing = qty_pf / pnt_parent_qty
            #
            #   theoretical_consumption: { comp_id: { pf: qty_teorica } }
            # ------------------------------------------------------------------
            theoretical_consumption = {}

            if li.template_id.compute_method == 'r8':
                for pf, qty_pf in produced_pf.items():
                    bom = self.env['mrp.bom'].search([
                        ('product_tmpl_id', '=', pf.id),
                    ], limit=1)
                    if not bom:
                        _logger.warning("[%s]   PF '%s': sin BoM, se omite.", method, pf.name)
                        continue
                    components = self._get_bom_components(bom, qty_pf)
                    comp_in_scope = {c: q for c, q in components.items() if c.id in raw_material_ids}
                    comp_out_scope = [c.name for c in components if c.id not in raw_material_ids]
                    _logger.warning("[%s]   PF '%s' (qty=%.2f): %d componentes en BoM, %d del tipo buscado, %d ignorados (%s)",
                                    method, pf.name, qty_pf, len(components),
                                    len(comp_in_scope), len(comp_out_scope), comp_out_scope)
                    for comp, comp_qty in comp_in_scope.items():
                        theoretical_consumption.setdefault(comp.id, {})
                        theoretical_consumption[comp.id][pf] = (
                            theoretical_consumption[comp.id].get(pf, 0.0) + comp_qty
                        )

            else:  # r9
                for pf, qty_pf in produced_pf.items():
                    packings_for_pf = packing_products.filtered(
                        lambda p: p.pnt_parent_id == pf
                    )
                    for packing in packings_for_pf:
                        bom = self.env['mrp.bom'].search([
                            ('product_tmpl_id', '=', packing.product_tmpl_id.id),
                        ], limit=1)
                        if not bom:
                            _logger.warning("[%s]   Packing '%s': sin BoM, se omite.", method, packing.name)
                            continue
                        qty_packing = qty_pf / (packing.pnt_parent_qty or 1.0)
                        factor = qty_packing / (bom.product_qty or 1.0)
                        lines_in_scope = bom.bom_line_ids.filtered(
                            lambda l: l.product_id.id in raw_material_ids
                        )
                        lines_out_scope = [l.product_id.name for l in bom.bom_line_ids
                                           if l.product_id.id not in raw_material_ids]
                        _logger.warning("[%s]   Packing '%s' → PF '%s' (qty_packing=%.4f): "
                                        "%d líneas en BoM, %d del tipo buscado, %d ignoradas (%s)",
                                        method, packing.name, pf.name, qty_packing,
                                        len(bom.bom_line_ids), len(lines_in_scope),
                                        len(lines_out_scope), lines_out_scope)
                        for line in lines_in_scope:
                            comp_qty = line.product_qty * factor
                            theoretical_consumption.setdefault(line.product_id.id, {})
                            theoretical_consumption[line.product_id.id][pf] = (
                                theoretical_consumption[line.product_id.id].get(pf, 0.0) + comp_qty
                            )

            _logger.warning("[%s] Componentes con consumo teórico: %d", method, len(theoretical_consumption))
            if not theoretical_consumption:
                _logger.warning("[%s] SALIDA: explosión de BoM no generó consumos del tipo '%s'.", method, component_types)
                return

            # ------------------------------------------------------------------
            # 4. Cálculo de pesos: peso(comp, PF) = consumo_teórico × standard_price
            #    El peso total es la base del reparto proporcional de li.balance.
            # ------------------------------------------------------------------
            relevant_comps = self.env['product.product'].browse(
                list(theoretical_consumption.keys())
            )
            comp_by_id = {comp.id: comp for comp in relevant_comps}

            # weights: { comp_id: { pf: peso } }
            weights = {}
            total_weight = 0.0
            for comp_id, pf_consumptions in theoretical_consumption.items():
                comp = comp_by_id[comp_id]
                weights[comp_id] = {}
                for pf, theoretical_qty in pf_consumptions.items():
                    w = theoretical_qty * comp.standard_price
                    weights[comp_id][pf] = w
                    total_weight += w

            if total_weight <= 0:
                return

            # ------------------------------------------------------------------
            # 5. Distribución proporcional y creación de apuntes analíticos.
            #    amount(comp, PF) = li.balance × peso(comp, PF) / peso_total
            #    Σ todos los apuntes = li.balance
            # ------------------------------------------------------------------
            product_field_id = self.env.company.product_field_id.name
            fixed_variable_field_id = self.env.company.fixed_variable_field_id.name
            department_field_id = self.env.company.department_field_id.name
            mrp_dept = self.env.company.analytic_mrp_department_id
            variable_account = self.env.company.analytic_variable_account_id

            for comp_id, pf_weights in weights.items():
                comp = comp_by_id[comp_id]
                comp_ref = f"[{comp.default_code}] " if comp.default_code else ""

                for pf, weight in pf_weights.items():
                    if not weight:
                        continue

                    proportion = weight / total_weight
                    coste_analitico = balance * proportion
                    proportion_pct = proportion * 100
                    theoretical_qty = theoretical_consumption[comp_id][pf]
                    pf_ref = f"[{pf.default_code}] " if pf.default_code else ""

                    note = (
                        f"Informe: {li.template_id.compute_method.upper()}\n"
                        f"Componente: {comp_ref}{comp.name} | Precio coste: {comp.standard_price:.4f}\n"
                        f"PF: {pf_ref}{pf.name}\n"
                        f"  Consumo teórico componente para este PF: {theoretical_qty:.4f}\n"
                        f"  Peso (consumo teórico × precio): {weight:.4f}\n"
                        f"  Peso total todos los pares (comp, PF): {total_weight:.4f}\n"
                        f"  Proporción: {proportion_pct:.4f}%\n"
                        f"  Balance a repartir: {balance:.2f}\n"
                        f"  Coste analítico = {balance:.2f} × {proportion_pct:.4f}% = {coste_analitico:.2f}"
                    )

                    analytic_account = self.check_or_create_analytic_account(pf)
                    self.env['account.analytic.line'].create({
                        'product_id': comp.id,
                        'name': f"{li.template_id.name} - {rec.name} | {comp.name} → {pf.name}",
                        'amount': -abs(coste_analitico),
                        product_field_id: analytic_account.id,
                        fixed_variable_field_id: variable_account.id,
                        'analytic_distribution_id': rec.id,
                        'analytic_distribution_template_id': li.template_id.id,
                        'analytic_distribution_note': note,
                    })
                    _logger.warning("[%s]   Apunte creado: %s → %s | %.2f€ (%.4f%%)",
                                    method, comp.name, pf.name, coste_analitico, proportion_pct)

    def _get_bom_components(self, bom, quantity):
        """Explota recursivamente una BoM y devuelve {product.product: qty}.

        - `quantity` es el número de unidades del producto padre a fabricar.
        - Se escala según `bom.product_qty` (la BoM puede estar definida para N
          unidades, no necesariamente 1).
        - Recursión: si una línea tiene `child_bom_id`, se desciende al sub-BoM
          (semi-fabricados); si no, el componente es hoja (materia prima o embalaje).
        """
        components = {}
        factor = quantity / (bom.product_qty or 1.0)
        for line in bom.bom_line_ids:
            comp_qty = line.product_qty * factor
            if line.child_bom_id:
                sub = self._get_bom_components(line.child_bom_id, comp_qty)
                for comp, qty in sub.items():
                    components[comp] = components.get(comp, 0.0) + qty
            else:
                components[line.product_id] = (
                    components.get(line.product_id, 0.0) + comp_qty
                )
        return components
