from odoo import _, api, fields, models
from odoo.exceptions import UserError

class ProductProduct(models.Model):
    _inherit = 'product.product'

    raw_efficiency = fields.Float('Raw efficiency', compute='_get_raw_efficiency_product_product')

    def _get_raw_efficiency_product_product(self):
        for record in self:
            raw, produced, efficiency = 0, 0, 1
            lots = self.env['stock.lot'].search([
                ('product_id','=',record.id),
                ('initial_received_quantity_computed','!=',0),
                ('product_id.wood_tracking','=',True),
            ])
            for lot in lots:
                raw += lot.initial_received_quantity_computed
                produced += lot.initial_received_quantity_computed * lot.raw_efficiency / 100
            if raw != 0:
                efficiency = produced / raw
            record['raw_efficiency'] = efficiency * 100

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    wood_tracking = fields.Boolean(related='material_id.wood_tracking')

   # CITES:
    is_cites = fields.Boolean('Is CITES', related='material_id.is_cites')
    material_type = fields.Selection(related='material_id.type')

    # FSC & CONTROL WOOD:
    is_fsc = fields.Boolean('Is FSC')
    fsc_type = fields.Selection(
        [("fsc", "FSC"), ("mix_credit", "Mix credit"), ("recycled", "Recycled"), ("mix_recycled", "Mix recycled"),('control','Control Wood')],
        string="FSC Type",
        copy=True,
    )
    fsc_mix_percentage = fields.Float('FSC Mix factor', help='Percent FSC produced without ERP control.')
    fsc_format_attribute_id = fields.Many2one('product.attribute', compute='_get_fsc_format_attribute')
    fsc_format_value_id = fields.Many2one('product.attribute.value', string='Format', store=True)

    # EUTR (normativa europea):
    eutr_nc_code = fields.Char('EUTR NC', compute='_get_eutr_nc_code', help='4 letf digits from Intrastat code.')

    # Eficiencia tras producir y mermas:
    raw_efficiency_pt = fields.Float('Raw efficiency', compute='_get_raw_efficiency_product_template')

    def _get_raw_efficiency_product_template(self):
        for record in self:
            rawvolume, producedvolume, efficiency = 0, 0, 1
            lots = self.env['stock.lot'].search([
                ('product_id.product_tmpl_id','=',record.id),
                ('initial_received_quantity_computed','!=',0),
                ('product_id.wood_tracking','=',True),
            ])
            for lot in lots:
                rawvolume += lot.initial_received_quantity_computed * lot.product_id.volume
                producedvolume += lot.initial_received_quantity_computed * lot.product_id.volume * lot.raw_efficiency / 100
            if rawvolume != 0:
                efficiency = producedvolume / rawvolume
            record['raw_efficiency_pt'] = efficiency * 100


    @api.constrains('fsc_type','fsc_mix_percentage')
    def _check_fsc_mix_percentage(self):
        if (self.fsc_type in ['mix_credit','mix_recycled'] and self.fsc_mix_percentage <= 0
                or self.fsc_type in ['mix_credit','mix_recycled'] and self.fsc_mix_percentage > 100):
            raise UserError('FSC percentage must be greater than 0 and maximum 1 !!')

    @api.depends('is_fsc')
    def _get_fsc_format_attribute(self):
        self.fsc_format_attribute_id = self.env.company.fsc_format_attribute_id.id

    @api.depends('intrastat_code_id')
    def _get_eutr_nc_code(self):
        for record in self:
            code = ""
            if record.intrastat_code_id.id: code = record.intrastat_code_id.code[:4]
            record['eutr_nc_code'] = code
