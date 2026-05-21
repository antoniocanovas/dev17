# -*- coding: utf-8 -*-
# Copyright
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import models, _, fields
from odoo.exceptions import UserError
from collections import defaultdict

_logger = logging.getLogger(__name__)


class MrpUnbuild(models.Model):
    _inherit = 'mrp.unbuild'

    def action_unbuild(self):
        # Si es un palet de Inplast, ejecutamos la lógica personalizada.
        # En caso contrario, se ejecuta la lógica estándar de Odoo.
        is_inplast_pallet = self._is_inplast_pallet_unbuild()
        if any(is_inplast_pallet.values()):
            return self._do_inplast_pallet_unbuild()
        
        return super().action_unbuild()

    def _is_inplast_pallet_unbuild(self):
        """Comprueba si la orden de deconstrucción es para un palet de Inplast."""
        res = {unbuild.id: False for unbuild in self}
        for unbuild in self:
            product = unbuild.product_id
            bom_tmpl = product.mrp_bom_template_id
            res[unbuild.id] = (
                product.pnt_product_type == 'packing'
                and bom_tmpl
                and 'pallet' in (bom_tmpl.type or '')
            )
        return res

    def _do_inplast_pallet_unbuild(self):
        """
        Ejecuta la deconstrucción personalizada para un palet de Inplast.
        """
        self.ensure_one()
        _logger.info("Autounbuild Inplast: Ejecutando deconstrucción de palet personalizada para '%s'", self.display_name)

        # --- 1. Validaciones y obtención de datos ---
        bom = self.bom_id
        if not bom:
            raise UserError(_("No Bill of Materials found for the product to unbuild."))

        pallet_line = bom.pallet_line_id
        if not pallet_line:
            raise UserError(_("The Bill of Materials does not have the 'pallet_line_id' field set."))

        related_lots = self.lot_id.related_boxes_ids
        use_bom_fallback = not related_lots

        # --- 2. Agrupar lotes por producto ---
        products_to_produce = defaultdict(list)
        if not use_bom_fallback:
            for lot in related_lots:
                products_to_produce[lot.product_id].append(lot)

        # --- 3. Creación de movimientos de stock ---
        all_moves = self.env['stock.move']
        
        production_location = self.product_id.property_stock_production
        if not production_location:
            raise UserError(_("Production location is not set on product '%s'.", self.product_id.display_name))

        # --- 3.1 Consumo del palet principal (dar de baja) ---
        consume_move = self._generate_move(self.product_id, self.product_qty, self.location_id, production_location)
        all_moves |= consume_move
        # Crear la línea de movimiento explícitamente para asegurar que se complete
        self.env['stock.move.line'].create({
            'move_id': consume_move.id,
            'product_id': self.product_id.id,
            'lot_id': self.lot_id.id,
            'qty_done': self.product_qty,
            'product_uom_id': self.product_uom_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': production_location.id,
        })

        # --- 3.2 Producción del material del palet ---
        pallet_product = pallet_line.product_id
        pallet_quantity = bom.product_qty * pallet_line.product_qty
        pallet_material_move = self._generate_move(pallet_product, pallet_quantity, production_location, self.location_dest_id)
        all_moves |= pallet_material_move

        # Crear la línea de movimiento para el material del palet, con o sin lote
        move_line_vals = {
            'move_id': pallet_material_move.id,
            'product_id': pallet_product.id,
            'qty_done': pallet_quantity,
            'product_uom_id': pallet_product.uom_id.id,
            'location_id': production_location.id,
            'location_dest_id': self.location_dest_id.id,
        }
        if pallet_product.tracking != 'none':
            if pallet_product.tracking == 'serial' and pallet_quantity != 1:
                raise UserError(_("Cannot produce multiple tracked-by-serial pallet materials. Quantity must be 1."))
            
            new_pallet_lot = self.env['stock.lot'].create({
                'name': f"{self.lot_id.name}-MAT",
                'product_id': pallet_product.id,
                'company_id': self.company_id.id,
            })
            move_line_vals['lot_id'] = new_pallet_lot.id
        self.env['stock.move.line'].create(move_line_vals)

        # --- 3.3 Producción de los componentes ---
        unbuild_mode = self.company_id.auto_unbuild_mode or 'lot'

        if use_bom_fallback:
            # Sin related_boxes_ids: buscar el producto packing tipo caja a través
            # del box_template_id del bom_template del palet y el pnt_parent_id del
            # producto principal.
            bom_tmpl = self.product_id.mrp_bom_template_id
            box_bom_template = bom_tmpl.box_template_id if bom_tmpl else False
            main_product_tmpl = self.product_id.product_tmpl_id.pnt_parent_id

            box_product = self.env['product.product']
            if box_bom_template and main_product_tmpl:
                box_product_tmpl = self.env['product.template'].search([
                    ('mrp_bom_template_id', '=', box_bom_template.id),
                    ('pnt_parent_id', '=', main_product_tmpl.id),
                ], limit=1)
                box_product = box_product_tmpl.product_variant_id

            if not box_product:
                raise UserError(_(
                    "The lot '%s' has no related boxes and no box packing product "
                    "could be found via the BOM template of the main product.",
                    self.lot_id.name
                ))
            box_quantity = self.product_id.pnt_box_qty
            component_move = self._generate_move(box_product, box_quantity, production_location, self.location_dest_id)
            all_moves |= component_move

            # Buscar lote existente con el mismo nombre; crear sólo si no existe
            new_lot = self.env['stock.lot'].search([
                ('name', '=', self.lot_id.name),
                ('product_id', '=', box_product.id),
                ('company_id', '=', self.company_id.id),
            ], limit=1)
            if not new_lot:
                new_lot = self.env['stock.lot'].create({
                    'name': self.lot_id.name,
                    'product_id': box_product.id,
                    'company_id': self.company_id.id,
                })
            self.env['stock.move.line'].create({
                'move_id': component_move.id,
                'product_id': box_product.id,
                'lot_id': new_lot.id,
                'qty_done': box_quantity,
                'product_uom_id': box_product.uom_id.id,
                'location_id': production_location.id,
                'location_dest_id': self.location_dest_id.id,
            })
        else:
            for product, lots in products_to_produce.items():
                quantity = len(lots)
                component_move = self._generate_move(product, quantity, production_location, self.location_dest_id)
                all_moves |= component_move

                if unbuild_mode == 'lot':
                    # Buscar lote existente; crear sólo si no existe
                    new_lot = self.env['stock.lot'].search([
                        ('name', '=', self.lot_id.name),
                        ('product_id', '=', product.id),
                        ('company_id', '=', self.company_id.id),
                    ], limit=1)
                    if not new_lot:
                        new_lot = self.env['stock.lot'].create({
                            'name': self.lot_id.name,
                            'product_id': product.id,
                            'company_id': self.company_id.id,
                        })
                    self.env['stock.move.line'].create({
                        'move_id': component_move.id,
                        'product_id': product.id,
                        'lot_id': new_lot.id,
                        'qty_done': quantity,
                        'product_uom_id': product.uom_id.id,
                        'location_id': production_location.id,
                        'location_dest_id': self.location_dest_id.id,
                    })
                else:
                    # serial_number: una línea por cada número de serie existente en related_boxes_ids
                    for lot in lots:
                        self.env['stock.move.line'].create({
                            'move_id': component_move.id,
                            'product_id': product.id,
                            'lot_id': lot.id,
                            'qty_done': 1.0,
                            'product_uom_id': product.uom_id.id,
                            'location_id': production_location.id,
                            'location_dest_id': self.location_dest_id.id,
                        })

        # --- 4. Validar y finalizar ---
        all_moves._action_confirm()
        all_moves._action_done()

        # Establecer trazabilidad: vincular las líneas consumidas con las producidas.
        # Sin este vínculo el informe de trazabilidad estándar de Odoo no puede
        # navegar de la operación de consumo a los componentes resultantes.
        produce_moves = all_moves - consume_move
        produced_move_line_ids = produce_moves.mapped('move_line_ids').filtered(
            lambda ml: ml.quantity > 0
        )
        consume_move.mapped('move_line_ids').write({
            'produce_line_ids': [(6, 0, produced_move_line_ids.ids)],
        })

        self.write({'state': 'done'})

        _logger.info("Autounbuild Inplast: Deconstrucción de palet '%s' completada.", self.display_name)
        return True

    def _generate_move(self, product, quantity, location_from, location_to):
        """Genera un movimiento de stock asociado a esta orden de deconstrucción."""
        return self.env['stock.move'].create({
            'name': self.name,
            'origin': self.name,
            'product_id': product.id,
            'product_uom_qty': quantity,
            'product_uom': product.uom_id.id,
            'location_id': location_from.id,
            'location_dest_id': location_to.id,
            'unbuild_id': self.id,
            'company_id': self.company_id.id,
        })
