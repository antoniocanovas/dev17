# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    # Para el caso de servicios subcontratados interesa que la descripción en compras y ventas sea compuesta por:
    # pedido de venta original + cliente en la dirección de la oferta + códigos de albarán.
    def update_product_subcontracted_name(self):
        for r in self:
            if r.product_id.service_to_purchase and r.sale_line_id:
                sale_order = r.sale_line_id.order_id

                # "nombres de albaranes de salida del pedido de venta"
                outgoing_pickings = sale_order.picking_ids.filtered(
                    lambda p: p.picking_type_id.code == 'outgoing' and p.state != 'cancel'
                )
                picking_names = ' '.join(outgoing_pickings.mapped('name'))

                # "nombre del pedido de venta"
                sale_order_name = sale_order.name

                # "nombre de la dirección de envío del pedido de venta"
                shipping_address_name = sale_order.partner_shipping_id.name if sale_order.partner_shipping_id else ''

                name_parts = [picking_names, sale_order_name, shipping_address_name]
                r.name = ' / '.join(filter(None, name_parts))
