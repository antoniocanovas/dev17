# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError

class EutrAudit(models.Model):
    _name = 'eutr.audit'
    _description = 'EUTR Audit'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char('Name', translate=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    date_from = fields.Date('From')
    date_to   = fields.Date('To')
    notes = fields.Html('Comments',  copy=False , translate=True)
    line_ids = fields.One2many('eutr.audit.line','eutr_audit_id', string='Lines')

    def compute_eutr_audit(self):
        # Objetivo es conseguir el listado de compra por MATERIAL y origen:
        self.line_ids.unlink()
        self.state = 'in_progress'
        # Materiales comprados que son madera (para evitar hacer líneas no compradas):
        purchase_sml = self.env['stock.move.line'].search([
            ('product_id.material_type','=','wood'),
            ('location_usage','=','supplier'),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('state','=', 'done'),
        ])
        purchase_materials = purchase_sml.product_id.material_id

        # Por cada material comprado, detectar orígenes y crear una línea por origen y material:
        for mat in purchase_materials:
            material_sml = self.env['stock.move.line'].search([
                ('product_id.material_id','=', mat.id),
                ('location_usage','=','supplier'),
                ('date', '>=', self.date_from),
                ('date', '<=', self.date_to),
                ('state','=', 'done'),
            ])

            # Validación de que todos los proveedores tienen provincia asignada:
            for sml in material_sml:
                if sml.picking_partner_id and not sml.picking_partner_id.state_id:
                    raise UserError('Please, set STATE to the partner: ' + sml.picking_partner_id.name)

            # Creación de línea por producto y origen:
            purchase_origins = material_sml.picking_partner_id.state_id
            material_products = material_sml.product_id
            for product in material_products:

                # INFO sobre trazabilidad del producto:
                eutr_cdc, eutr_cl = False, False
                if product.is_fsc or product.is_cites:
                    eutr_cl = True
                if product.is_fsc and product.fsc_type not in ['wood_control']:
                    eutr_cdc = True

                # Cálculo del volúmen y creación de línea de informe:
                for origin in purchase_origins:
                    # Calcular el volumen total comprado en volúmen TM3:
                    volume = 0
                    for sml in material_sml:
                        if (sml.product_id == product) and (origin == sml.picking_partner_id.state_id):
                            volume += sml.quantity * product.volume / 1000
                    # Crear la línea:
                    if volume > 0:
                        self.env['eutr.audit.line'].create({
                            'eutr_audit_id': self.id,
                            'product_id': product.id,
                            'state_id': sml.picking_partner_id.state_id.id,
                            'volume': volume,
                            'eutr_cl': eutr_cl,
                            'eutr_cdc': eutr_cdc,
                        })
