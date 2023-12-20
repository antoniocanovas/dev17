from odoo import _, api, fields, models
from datetime import date

import logging
_logger = logging.getLogger(__name__)


class ProductPricelist(models.Model):
    _name = 'product.pricelist'
    _inherit = ['product.pricelist', 'mail.thread', 'mail.activity.mixin']

    pnt_tracking_date = fields.Date('Tracking date', store=True, copy=False)
    pnt_pending_update = fields.Boolean('Pending update', store=True, copy=False, default=False)

    # Productos en la lista de precios, para ser usados como exclusivamente disponibles en ventas y facturas:
    @api.depends('item_ids.product_tmpl_id')
    def _get_pricelist_products(self):
        products = []
        for li in self.item_ids:
            if (li.product_tmpl_id.id) and not (li.product_id.id):
                pnt_product_ids = self.env['product.product'].search([('product_tmpl_id', '=', li.product_tmpl_id.id)])
                for pro in pnt_product_ids: products.append(pro.id)
            else:
                products.append(li.product_id.id)
        self.pnt_product_ids = [(6,0,products)]
    pnt_product_ids = fields.Many2many('product.product', store=True, compute='_get_pricelist_products')

    # Categorías utilizadas en esta tarifa:
    @api.depends('item_ids.product_tmpl_id.categ_id')
    def _get_product_categs(self):
        categs = []
        for li in self.item_ids:
            if (li.product_tmpl_id.categ_id.id) not in categs:
                categs.append(li.product_tmpl_id.categ_id.id)
        self.pnt_product_categ_ids = [(6,0,categs)]
    pnt_product_categ_ids = fields.Many2many('product.category', string='Raw products', store=False,
                                           compute='_get_product_categs')


    # Crear una nota con los precios que han cambiado en la tarifa, desde botón o acción planificada:
    def pricelist_update_tracking(self):
        item_tracking = ""
        now = date.today()

        for li in self.item_ids:
            if (li.pnt_new_price != li.fixed_price) and (li.pnt_product_state == True):
                categ = li.product_tmpl_id.categ_id
                name = li.product_tmpl_id.name
                if li.product_id.id: name = li.product_id.name
                item_tracking += "<p>" + name + \
                                 ", Previous: " + str(li.fixed_price) + \
                                 ", New: " + str(li.pnt_new_price) + \
                                 ", Raw: " + str(categ.pnt_i0) + \
                                 ", Comercial i1, i2, i3: " + \
                                 str(categ.pnt_i1) + ", " + str(categ.pnt_i2) + ", " + str(categ.pnt_i3) + \
                                 "</p>"
                li.write({'pnt_tracking_date':now, 'fixed_price':li.pnt_new_price})

        if item_tracking != "":
            new_note = self.env['mail.message'].create({'body': item_tracking,
                                                        'message_type': 'comment',
                                                        'model': 'product.pricelist',
                                                        'res_id': self.id,
                                                        })
        self.write({'pnt_tracking_date':now, 'pnt_pending_update':False})


    # Recalcular precios de tarifa en base a parámetros establecidos:
    def products_pricelist_recalculation(self):
        for li in self.item_ids:
            product = li.product_tmpl_id
            categ = product.categ_id
            fault_percent = categ.pnt_mrp_fault_percent
            last_price = li.fixed_price
            raw_increment = categ.pnt_i0

            # Tarifa/peso en familia:
            pricelist_weight = product.categ_id.pnt_pricelist_weight

            # Incremento de precio debido al coste de materia prima (se consideran defectuosos):
            net_price = pricelist_weight * (raw_increment / 1000) * (1 + fault_percent/100) + (last_price * 1000)

            increment1 = net_price * (categ.pnt_i1 / 100)
            increment2 = pricelist_weight * (categ.pnt_i2 / 1000) * (1 + fault_percent/100)
            price1000 = net_price + increment1 + increment2 + categ.pnt_i3
            unit_price = price1000 / 1000
            li.write({'pnt_new_price':unit_price, 'pnt_tracking_date':date.today()})
        self.pnt_pending_update = True