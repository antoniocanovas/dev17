# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api
from odoo.exceptions import UserError

class FscAudit(models.Model):
    _name = 'fsc.audit'
    _description = 'FSC Audit'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char('Name', translate=True, tracking=True)
    auditor_id = fields.Many2one('res.partner', string='Auditor', tracking=True)
    audit_date = fields.Date(string='Audit Date', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    date_from = fields.Date('From')
    date_to   = fields.Date('To')
    notes = fields.Html('Comments',  copy=False , translate=True)
    line_ids = fields.One2many('fsc.audit.line','fsc_audit_id', string='Lines')

    def compute_fsc_audit(self):
        # Objetivo es conseguir el rendimiento por MATERIAL COMPRADO indicando formato origen:
        self.line_ids.unlink()
        self.state = 'in_progress'
        # Materiales que tienen trazabidad FSC:
        fsc_products = self.env['product.product'].search([('wood_tracking','=',True),('is_fsc','=',True)])
        fsc_materials = fsc_products.material_id

        # 1. Creación de líneas de informe consolidadas:
        for material in fsc_materials:
            self.env['fsc.audit.line'].create({
                'fsc_audit_id': self.id,
                'material_id':  material.id,
            })

        # 2. Creación de líneas de detalle fsc.audit.product (cada una es un MATERIAL distinto):
        for li in self.line_ids:
            # Productos de este material con trazabilidad FSC:
            products = self.env['product.product'].search([
                ('material_id','=',li.material_id.id),
                ('wood_tracking','=',True),
                ('is_fsc','=',True),
            ])

            for prod in products:
                # Crear línea de producto para stock_start_vol: tipo stock_start, volume:
                stock_start_vol = prod.with_context(to_date=self.date_from).qty_available * prod.volume
                self.env['fsc.audit.product'].create({
                    'fsc_audit_line_id': li.id,
                    'product_id': prod.id,
                    'volume': stock_start_vol,
                    'type': 'stock_start',
                })

                # Crear línea de producto para stock_final_vol: tipo stock_final, volume
                stock_final_vol = prod.with_context(to_date=self.date_to).qty_available * prod.volume
                self.env['fsc.audit.product'].create({
                    'fsc_audit_line_id': li.id,
                    'product_id': prod.id,
                    'volume': stock_final_vol,
                    'type': 'stock_final',
                })

                # Crear línea de producto para purchase_vol (considerar devoluciones): tipo purchase, volume
                # Primero las compras:
                sml_purchases = self.env['stock.move.line'].search([
                    ('product_id','=',prod.id),
                    ('location_id.usage','=','supplier'),
                    ('date','>=', self.date_from),
                    ('date', '<=', self.date_to),
                    ('state', '=', 'done'),
                ])
                sml_purchases_vol = sum(sml_purchases.mapped('quantity')) * prod.volume
                # Ahora las devoluciones:
                sml_purchases_return = self.env['stock.move.line'].search([
                    ('product_id', '=', prod.id),
                    ('location_dest_id.usage', '=', 'supplier'),
                    ('date', '>=', self.date_from),
                    ('date', '<=', self.date_to),
                    ('state', '=', 'done'),
                ])
                sml_purchases_return_vol = sum(sml_purchases_return.mapped('quantity')) * prod.volume
                self.env['fsc.audit.product'].create({
                    'fsc_audit_line_id': li.id,
                    'product_id': prod.id,
                    'volume': sml_purchases_vol - sml_purchases_return_vol,
                    'type': 'purchase',
                })

                # Crear línea de producto para sale_vol (considerar devoluciones): tipo sale, volume
                sml_sales = self.env['stock.move.line'].search([
                    ('product_id','=',prod.id),
                    ('location_dest_id.usage','=','customer'),
                    ('date','>=', self.date_from),
                    ('date', '<=', self.date_to),
                    ('state', '=', 'done'),
                ])
                sml_sales_vol = sum(sml_sales.mapped('quantity')) * prod.volume
                # Ahora las devoluciones:
                sml_sales_return = self.env['stock.move.line'].search([
                    ('product_id', '=', prod.id),
                    ('location_id.usage', '=', 'customer'),
                    ('date', '>=', self.date_from),
                    ('date', '<=', self.date_to),
                    ('state', '=', 'done'),
                ])
                sml_sales_return_vol = sum(sml_sales_return.mapped('quantity')) * prod.volume
                self.env['fsc.audit.product'].create({
                    'fsc_audit_line_id': li.id,
                    'product_id': prod.id,
                    'volume': sml_sales_vol - sml_sales_return_vol,
                    'type': 'sale',
                })

        # 2. Creación de líneas de detalle fsc.audit.product (cada una es un MATERIAL distinto):
        for li in self.line_ids:
            stock_start_vol, stock_final_vol, purchase_vol, sale_vol, efficiency = 0, 0, 0, 0, 100

            # STOCK_START_VOL:
            fsc_audit_product_stock_start_vol = self.env['fsc.audit.product'].search([
                ('material_id','=',li.material_id.id),
                ('type','=','stock_start'),
            ])
            if fsc_audit_product_stock_start_vol.ids:
                stock_start_vol = sum(fsc_audit_product_stock_start_vol.mapped('volume'))

            # STOCK_FINAL_VOL:
            fsc_audit_product_stock_final_vol = self.env['fsc.audit.product'].search([
                ('material_id','=',li.material_id.id),
                ('type','=','stock_final'),
            ])
            if fsc_audit_product_stock_final_vol.ids:
                stock_final_vol = sum(fsc_audit_product_stock_final_vol.mapped('volume'))

            # PURCHASE_VOL:
            fsc_audit_product_purchase_vol = self.env['fsc.audit.product'].search([
                ('material_id','=',li.material_id.id),
                ('type','=','purchase'),
            ])
            if fsc_audit_product_purchase_vol.ids:
                purchase_vol = sum(fsc_audit_product_purchase_vol.mapped('volume'))

            # SALE_VOL:
            fsc_audit_product_sale_vol = self.env['fsc.audit.product'].search([
                ('material_id','=',li.material_id.id),
                ('type','=','sale'),
            ])
            if fsc_audit_product_sale_vol.ids:
                sale_vol = sum(fsc_audit_product_sale_vol.mapped('volume'))

            # EFFICIENCY:
            if purchase_vol + stock_start_vol > 0:
                efficiency = (sale_vol + stock_final_vol) / (purchase_vol + stock_start_vol)

            li.write({
                'stock_start_vol': stock_start_vol,
                'stock_final_vol': stock_final_vol,
                'purchase_vol': purchase_vol,
                'sale_vol': sale_vol,
                'efficiency': efficiency,
            })

    # ----------- CAMPOS PARA LOS BOTONES O2M DEL FORMULARIO: ----------------
    fsc_audit_product_line_count = fields.Integer(
        compute='_compute_fsc_audit_product_line_count',
        string="Stock" # Etiqueta que se puede usar en el botón
    )
    @api.depends('line_ids.fsc_audit_product_ids')
    def _compute_fsc_audit_product_line_count(self):
        for record in self:
            lines = self.env['fsc.audit.product'].search([('fsc_audit_id','=',record.id)])
            record.fsc_audit_product_line_count = len(lines)

