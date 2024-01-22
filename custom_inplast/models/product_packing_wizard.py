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
    pnt_pallet_box_id  = Many2one('product.template', string='Pallet box', domain="[('pnt_product_type','=','packaging')]")
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
            # Crear caja
            dye = ""
            if record.name.pnt_product_dye_id.id: dye = " " + record.name.pnt_product_dye_id.name
            name = record.name.name + dye + " - Caja " + str(record.pnt_box_base_qty)
            exist = self.env['product.template'].search([('name', '=', name)])
            routemrp = self.env.ref('mrp.route_warehouse0_manufacture')
            if not exist.id:
                newpacking = self.env['product.template'].create({
                    'name': name,
                    'pnt_product_type': 'packing',
                    'pnt_parent_id': record.name.id,
                    'pnt_parent_qty': record.pnt_box_base_qty,
                    'detailed_type': 'product',
                    'list_price': record.name.list_price * record.pnt_box_base_qty,
                    'pnt_plastic_weight': record.name.pnt_plastic_weight * record.pnt_box_base_qty,
                    'standard_price': record.name.standard_price * record.pnt_box_base_qty,
                    'sale_ok': True,
                    'purchase_ok': False,
                    'route_ids': [(6, 0, [routemrp.id])]
                })
            else:
                raise UserError('Este producto ya existe.')

            # Crear lista de materiales
            newproductldm = self.env['mrp.bom'].create({
                'code': name,
                'product_tmpl_id': newpacking.id,
                'type': 'normal',
            })

            if record.pnt_type == 'box':
                # Crear componentes de la lista de materiales para CAJAS:
                product = self.env['product.product'].search([('product_tmpl_id','=', record.pnt_box_type_id.id)])[0]
                newbomboxline  = self.env['mrp.bom.line'].create(
                    {'product_id': product.id, 'product_qty': 1, 'bom_id': newproductldm.id })
                bag = self.env['product.product'].search([('product_tmpl_id','=', record.pnt_box_bag_id.id)])[0]
                newbomboxbag   = self.env['mrp.bom.line'].create(
                    {'product_id': bag.id, 'product_qty': record.pnt_box_bag_qty, 'bom_id': newproductldm.id})
                label = self.env['product.product'].search([('product_tmpl_id','=', record.pnt_box_label_id.id)])[0]
                newbomboxlabel = self.env['mrp.bom.line'].create(
                    {'product_id': label.id, 'product_qty': record.pnt_box_label_qty, 'bom_id': newproductldm.id})
                seal = self.env['product.product'].search([('product_tmpl_id', '=', record.pnt_box_seal_id.id)])[0]
                newbomboxseal  = self.env['mrp.bom.line'].create(
                    {'product_id': seal.id, 'product_qty': record.pnt_box_seal_qty, 'bom_id': newproductldm.id})

                # Crear en tarifas:
                pricelist = []
                pricelist_item = self.env['product.pricelist.item'].search([('product_tmpl_id','=', record.name.id)])
                for item in pricelist_item:
                    if item.pricelist_id.id not in pricelist:
                        pricelistitem = self.env['product.pricelist.item'].create({
                            'pricelist_id': item.pricelist_id.id,
                            'product_tmpl_id': newpacking.id,
                            'applied_on': '1_product',
                            'compute_price': 'fixed',
                            'fixed_price': newpacking.list_price,
                        })
                        pricelist.append(item.pricelist_id.id)







            else:
                # Crear componentes de la lista de materiales para PALETS:
                product = self.env['product.product'].search([('product_tmpl_id', '=', record.pnt_pallet_type_id.id)])[0]
                newbomboxline = self.env['mrp.bom.line'].create(
                    {'product_id': product.id, 'product_qty': 1, 'bom_id': newproductldm.id})
                bag = self.env['product.product'].search([('product_tmpl_id', '=', record.pnt_box_bag_id.id)])[0]
                newbomboxbag = self.env['mrp.bom.line'].create(
                    {'product_id': bag.id, 'product_qty': record.pnt_box_bag_qty, 'bom_id': newproductldm.id})
                label = self.env['product.product'].search([('product_tmpl_id', '=', record.pnt_box_label_id.id)])[
                    0]
                newbomboxlabel = self.env['mrp.bom.line'].create(
                    {'product_id': label.id, 'product_qty': record.pnt_box_label_qty, 'bom_id': newproductldm.id})
                seal = self.env['product.product'].search([('product_tmpl_id', '=', record.pnt_box_seal_id.id)])[0]
                newbomboxseal = self.env['mrp.bom.line'].create(
                    {'product_id': seal.id, 'product_qty': record.pnt_box_seal_qty, 'bom_id': newproductldm.id})

                # Crear en tarifas:
                pricelist = []
                pricelist_item = self.env['product.pricelist.item'].search(
                    [('product_tmpl_id', '=', record.name.id)])
                for item in pricelist_item:
                    if item.pricelist_id.id not in pricelist:
                        pricelistitem = self.env['product.pricelist.item'].create({
                            'pricelist_id': item.pricelist_id.id,
                            'product_tmpl_id': newpacking.id,
                            'applied_on': '1_product',
                            'compute_price': 'fixed',
                            'fixed_price': newpacking.list_price,
                        })
                        pricelist.append(item.pricelist_id.id)

