from odoo import _, api, fields, models
from odoo.exceptions import UserError

class ProductPackingWizard(models.TransientModel):
    _name = 'product.packing.wizard'
    _description = 'Product Packing Wizard'

    #Campos generales
    name = fields.Many2one('product.template', string='Product')
    pnt_type = fields.Selection([('box','Box'),('pallet','Pallet')], string='Packing type')
    #Cajas:

    pnt_box_type_id = fields.Many2one('product.template', string='Box', domain="[('pnt_product_type','=','packaging')]")
    pnt_box_base_qty = fields.Integer('Base qty')
    pnt_box_bag_id = fields.Many2one('product.template', string='Box Bag', domain="[('pnt_product_type','=','packaging')]",
                                     default=lambda self: self.env.company.pnt_box_bag_id.id)
    pnt_box_bag_qty = fields.Integer('Bags qty', default="1")
    pnt_box_label_id = fields.Many2one('product.template', string='Box Label', domain="[('pnt_product_type','=','packaging')]")
    pnt_box_label_qty = fields.Integer('Label qty', default="1")
    pnt_box_seal_id = fields.Many2one('product.template', string='Box Seal', domain="[('pnt_product_type','=','packaging')]")
    pnt_box_seal_qty = fields.Integer('Seal qty')

    #Palets:
    pnt_pallet_type_id = fields.Many2one('product.template', string='Pallet', domain="[('pnt_product_type','=','packaging')]")
    pnt_pallet_box_qty = fields.Integer('Box qty', default="24")
    pnt_pallet_film_id = fields.Many2one('product.template', string='Pallet Film', domain="[('pnt_product_type','=','packaging')]")
    pnt_pallet_film_qty = fields.Integer('Film qty')
    pnt_pallet_seal_id = fields.Many2one('product.template', string='Pallet seal', domain="[('pnt_product_type','=','packaging')]")
    pnt_pallet_seal_qty = fields.Integer('Pallet seal qty')
    pnt_pallet_label_id = fields.Many2one('product.template', string='Pallet Label', domain="[('pnt_product_type','=','packaging')]")
    pnt_pallet_label_qty = fields.Integer('Pallet Label qty', default="1")
    pnt_picking_label_id = fields.Many2one('product.template', string='Picking Label', domain="[('pnt_product_type','=','packaging')]")
    pnt_picking_label_qty = fields.Integer('Picking Label qty', default="1")

    def create_packing_products(self):
        for record in self:
            if record.pnt_type == 'box':
                # Crear caja
                dye = ""
                if record.name.pnt_product_dye_id.id: dye= " " + record.name.pnt_product_dye_id.name
                name = record.name.name + " - Caja " + str(record.pnt_box_base_qty) + dye
                exist = self.env['product.template'].search([('name','=', name)])
                if not exist.id:
                    newbox = self.env['product.template'].create({
                        'name': name,
                        'pnt_product_type': 'packing',
                        'detailed_type': 'product',
                        'list_price': record.name.list_price * record.pnt_box_base_qty,
                        'pnt_plastic_weight': record.name.pnt_plastic_weight * record.pnt_box_base_qty,
                        'standard_price': record.name.standard_price * record.pnt_box_base_qty,
                    })
                else:
                    raise UserError('Este producto ya existe.')
                # Crear lista de materiales
                # Crear en tarifas
                return True
            else:
                # Crear producto paletizado
                # Crear lista de materiales
                # Crear en tarifas
                return True
        return True