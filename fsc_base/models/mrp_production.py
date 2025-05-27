from odoo import _, api, fields, models
from odoo.exceptions import UserError

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    material_id = fields.Many2one(related='product_id.material_id', store=True)
    wood_tracking = fields.Boolean(related='product_id.wood_tracking')
    fsc_efficiency = fields.Float('FSC efficiency')

    # Para control de purezo FSC hay que revisar materiales de entrada y asignar % a la orden de producción.
    # Si el material viene de otra orden => el de la orden; si es comprado hay tres opciones:
    # a) 100% si type es FSC,
    # b) Porcentaje directo del producto si es type MIX y el material no es por porcentaje fijo.
    fsc_percentage = fields.Float('FSC percentage')
    fsc_origin_format_value_id = fields.Many2one('product.attribute.value', string='Origin format', store=True)

    def _get_fsc_efficiency_and_percentage(self):
        for record in self:
            # Para el cálculo de eficiencia FSC en base a pérdidas por corte y desechos:
            rawvolume, producedvolume, efficiency, fsc_percentage = 0, 0, 1, 0

            # Para el cálculo de porcentaje FSC en la entrada de producción que se guardará en el mrp.production:
            fscvolume, incomevolume  = 0, 0

            # move_raw_ids son entradas, move_finished_ids son todas las salidas, move_byproduct_ids sólo los subproductos:
            for sm in record.move_raw_ids:
                if sm.product_id.wood_tracking:
                    for sml in sm.move_line_ids:
                        factor, fsc_percentage = 1, 0
                        product = sml.product_id

                        # Valores por defecto para productos FSC:
                        if product.fsc_type in ['fsc', 'recycled']:
                            fsc_percentage = 100
                        elif product.fsc_type in ['mix_credit', 'mix_recycled']:
                            fsc_percentage = product.fsc_mix_percentage

                        # Buscamos la orden de producción para este producto y lote por si encontramos eficiencia previa:
                        smlproduced = self.env['stock.move.line'].search([
                            ('product_id', '=', product.id),
                            ('move_id.production_id', '!=', False),
                            ('location_id.usage', '=', 'production'),
                            ('lot_id', '=', sml.lot_id.id),
                        ], limit=1)
                        # Eficiencia en la producción anterior:
                        if smlproduced.id and smlproduced.move_id.production_id.fsc_efficiency > 0:
                            factor = smlproduced.move_id.production_id.fsc_efficiency / 100

                        # Para productos que fluctuan su certificación FSC, sobreescribimos los valores por defecto:
                        if smlproduced.id and product.fsc_type in ['mix_credit', 'mix_recycled']:
                            fsc_percentage = smlproduced.move_id.production_id.fsc_percentage

                        rawvolume += product.volume * sml.quantity / factor
                        incomevolume += product.volume * sml.quantity
                        fscvolume += product.volume * sml.quantity * fsc_percentage / 100

            if incomevolume > 0:
                fsc_percentage = fscvolume / incomevolume * 100
                #print('fsc_percentage: ' + str(fsc_percentage) + " fscvolume: " + str(fscvolume)+ " incomevolume: " + str(incomevolume))

            # Si un producto está marcado como desecho no cuenta como volumen producido:
            for li in record.move_finished_ids:
                if li.product_id.wood_tracking:
                    producedvolume += li.product_id.volume * li.quantity
            if rawvolume > 0:
                efficiency = producedvolume / rawvolume * 100
            record.write({'fsc_efficiency': round(efficiency,2), 'fsc_percentage':round(fsc_percentage,2)})

    def _fsc_update_mrp_production(self):
        for rec in self:
            if rec.state not in ['draft'] and rec.wood_tracking:
                # Actualizar datos de eficiencia:
                rec._get_fsc_efficiency_and_percentage()

                # Chequear en productos de entrada similar formato FSC ("W"), requerido para AUDITORÍA FSC:
                if rec.state not in 'draft':
                    materials, format = set(), set()
                    for sml in rec.move_raw_ids.move_line_ids:
                        if sml.product_id.material_type == 'wood':
                            materials.add(sml.product_id.material_id.id)
                        if sml.product_id.is_fsc:
                            format.add(sml.product_id.fsc_format_value_id.id)

                    if len(format) > 1 or len(materials) > 1:
                        raise UserError('Para la trazabilidad FSC, todos los productos origen en su compra han de ser'
                                        'del mismo MATERIAL y FORMATO W, haga distintas órdenes de producción.')

                # Chequear si los productos finales son 100% FSC y los de entrada son también 100%:
                if rec.state == 'done' and rec.fsc_percentage < 100:
                    products = rec.finished_move_line_ids.product_id
                    product_names = ""
                    for product in products:
                        if product.fsc_type in ['fsc','recycled']:
                            product_names += "[" + product.name + "] "
                    if product_names != "":
                        raise UserError('Los productos a fabricar ' + product_names + ' requieren que todos materiales sean FSC 100%')

                # Actualizar el W original en producción y cada lote producido (producidos previstos y subproductos):
                if rec.state == 'done' and  len(format) == 1:
                    rec.write({'fsc_origin_format_value_id':format})
                    for sml in rec.finished_move_line_ids:
                        if sml.lot_id:
                            sml.lot_id.write({'fsc_origin_format_value_id':format})