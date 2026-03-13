# -*- coding: utf-8 -*-
# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
#
# R22: Distribución de gastos comerciales entre productos vendidos.
#
# Objetivo:
#   Repartir el coste del balance (cuentas contables de la plantilla) entre los
#   productos base (tapones / asas) vendidos, creando un apunte analítico por
#   producto base y destino de venta (España, UE, Extracomunitario).
#
# Fuente del coste:
#   li.balance  →  saldo de las cuentas contables configuradas en la plantilla.
#
# Base de reparto:
#   1. Se obtienen todas las líneas de factura de venta del período cuyo producto
#      es de tipo 'packing'.
#   2. Las líneas se clasifican por destino:
#        - España       (partner_id.country_id.code == 'ES')
#        - UE           (país en grupo Europe, excluyendo España)
#        - Extracom.    (resto)
#   3. Para cada destino se calcula el importe facturado total y su porcentaje
#      sobre el total general de facturación packing.
#   4. La parte del balance que corresponde a cada destino =
#        balance × (facturado_destino / facturado_total)
#   5. Dentro de cada destino se reparte proporcionalmente al importe facturado
#      de cada producto base (pnt_parent_id del packing):
#        coste_base = balance_destino × (facturado_base_en_destino / facturado_destino)
#   6. Las unidades de producto base vendidas =
#        Σ línea.quantity × packing.pnt_parent_qty
#      (se incluyen en la nota a modo informativo).
#
# Salida:
#   Un apunte analítico (account.analytic.line) por cada par
#   (producto_base, destino) con importe negativo igual al coste asignado.
#   El nombre del apunte incluye "Gastos comerciales ESPAÑA / UE / EXTRACOMUNITARIO".
from odoo import models
import logging
_logger = logging.getLogger(__name__)


class AnalyticDistribution(models.Model):
    _inherit = 'analytic.distribution'

    def compute_r22(self, li):
        """Distribuye li.balance entre los productos base vendidos como packing,
        segmentando por destino (España, UE, Extracomunitario) y ponderando por
        el importe facturado de cada producto base en cada segmento.

        Parámetros:
            li  (analytic.distribution.line): línea con el template R22 que
                contiene el balance contable a distribuir.
        """
        for rec in self:
            method = 'R22'
            balance = li.balance
            _logger.warning("[%s] Iniciando cálculo. balance=%.2f", method, balance)
            if not balance:
                _logger.warning("[%s] SALIDA: balance es 0 o nulo.", method)
                return

            date_from = rec.date_from
            date_to = rec.date_to
            _logger.warning("[%s] Periodo: %s → %s", method, date_from, date_to)

            # ------------------------------------------------------------------
            # 1. Líneas de factura de venta confirmadas del período para
            #    productos de tipo 'packing'.
            # ------------------------------------------------------------------
            invoice_lines = self.env['account.move.line'].search([
                ('move_id.move_type', '=', 'out_invoice'),
                ('move_id.state', '=', 'posted'),
                ('move_id.invoice_date', '>=', date_from),
                ('move_id.invoice_date', '<=', date_to),
                ('product_id.pnt_product_type', '=', 'packing'),
            ])
            _logger.warning("[%s] Líneas de factura packing encontradas: %d", method, len(invoice_lines))
            if not invoice_lines:
                _logger.warning("[%s] SALIDA: no hay líneas de factura en el periodo.", method)
                return

            # ------------------------------------------------------------------
            # 2. Clasificación de líneas por destino usando el grupo Europe de
            #    Odoo como referencia para los países de la UE.
            # ------------------------------------------------------------------
            eu_group = self.env.ref('base.europe', raise_if_not_found=False)
            eu_country_ids = set(eu_group.country_ids.ids) if eu_group else set()

            def _get_segment(line):
                country = line.move_id.partner_id.country_id
                if not country:
                    return 'extra'
                if country.code == 'ES':
                    return 'es'
                if country.id in eu_country_ids:
                    return 'eu'
                return 'extra'

            # ------------------------------------------------------------------
            # 3. Acumulación de importes y unidades por (segmento, producto_base).
            #    segment_data: { segmento: { base_product: {'amount': x, 'qty': y} } }
            #    total_amount: facturación global de todos los packings.
            # ------------------------------------------------------------------
            total_amount = 0.0
            segment_data = {}

            for line in invoice_lines:
                packing = line.product_id  # product.product
                base_tmpl = packing.pnt_parent_id  # product.template
                if not base_tmpl:
                    _logger.warning("[%s]   Packing '%s' sin pnt_parent_id, ignorado.", method, packing.name)
                    continue

                segment = _get_segment(line)
                line_amount = line.price_subtotal
                # Unidades en términos del producto base
                line_qty = line.quantity * (packing.pnt_parent_qty or 1.0)

                bp = segment_data.setdefault(segment, {}).setdefault(
                    base_tmpl, {'amount': 0.0, 'qty': 0.0}
                )
                bp['amount'] += line_amount
                bp['qty'] += line_qty
                total_amount += line_amount

            _logger.warning("[%s] Facturación total packing: %.2f | Segmentos activos: %s",
                            method, total_amount, list(segment_data.keys()))

            if total_amount <= 0:
                _logger.warning("[%s] SALIDA: facturación total es 0.", method)
                return

            # ------------------------------------------------------------------
            # 4. Campos de la línea analítica (misma convención que otros informes).
            # ------------------------------------------------------------------
            product_field_id = self.env.company.product_field_id.name
            fixed_variable_field_id = self.env.company.fixed_variable_field_id.name
            department_field_id = self.env.company.department_field_id.name
            sale_dept = self.env.company.analytic_sale_department_id
            variable_account = self.env.company.analytic_variable_account_id

            segment_labels = {
                'es': 'ESPAÑA',
                'eu': 'UE',
                'extra': 'EXTRACOMUNITARIO',
            }

            # ------------------------------------------------------------------
            # 5. Para cada segmento: calcular balance asignado y distribuirlo
            #    entre los productos base proporcionalmente al importe facturado.
            # ------------------------------------------------------------------
            for segment, base_products in segment_data.items():
                segment_total = sum(bp['amount'] for bp in base_products.values())
                if not segment_total:
                    continue

                segment_pct = segment_total / total_amount
                segment_balance = balance * segment_pct
                label = segment_labels.get(segment, segment.upper())

                _logger.warning("[%s] Segmento %s: facturado=%.2f (%.4f%%) → balance=%.2f",
                                method, label, segment_total, segment_pct * 100, segment_balance)

                for base_tmpl, data in base_products.items():
                    if not data['amount']:
                        continue

                    proportion = data['amount'] / segment_total
                    cost = segment_balance * proportion
                    qty = data['qty']
                    cost_per_unit = (cost / qty) if qty else 0.0

                    # product.product para el campo product_id del apunte (igual
                    # que R10/R11 y R8/R9: check_or_create recibe el template,
                    # pero product_id recibe un product.product)
                    base_product = base_tmpl.product_variant_ids[:1]

                    note = (
                        f"Informe: {method}\n"
                        f"Segmento: {label}\n"
                        f"Producto base: {base_tmpl.name}\n"
                        f"─── Facturación ───\n"
                        f"  Facturación total packing: {total_amount:.2f}\n"
                        f"  Facturación segmento {label}: {segment_total:.2f} ({segment_pct * 100:.4f}%)\n"
                        f"  Facturación producto en segmento: {data['amount']:.2f}\n"
                        f"─── Reparto ───\n"
                        f"  Balance a repartir: {balance:.2f}\n"
                        f"  Balance segmento = {balance:.2f} × {segment_pct * 100:.4f}% = {segment_balance:.2f}\n"
                        f"  Proporción en segmento: {proportion * 100:.4f}%\n"
                        f"  Coste asignado = {segment_balance:.2f} × {proportion * 100:.4f}% = {cost:.2f}\n"
                        f"─── Unidades ───\n"
                        f"  Unidades vendidas (prod. base): {qty:.2f}\n"
                        f"  Coste/unidad = {cost:.2f} / {qty:.2f} = {cost_per_unit:.4f}"
                    )

                    analytic_account = self.check_or_create_analytic_account(base_tmpl)
                    self.env['account.analytic.line'].create({
                        'product_id': base_product.id if base_product else False,
                        'name': (
                            f"Gastos comerciales {label} - "
                            f"{li.template_id.name} - {rec.name} | {base_tmpl.name}"
                        ),
                        'amount': -abs(cost),
                        product_field_id: analytic_account.id,
                        fixed_variable_field_id: variable_account.id,
                        department_field_id: sale_dept.id if sale_dept else False,
                        'analytic_distribution_id': rec.id,
                        'analytic_distribution_template_id': li.template_id.id,
                        'analytic_distribution_note': note,
                    })
                    _logger.warning("[%s]   Apunte creado: %s | %s → %.2f€ (%.4f%%) / %.2f u.base",
                                    method, label, base_tmpl.name, cost, proportion * 100, qty)
