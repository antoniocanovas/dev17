# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api

class FscAuditLine(models.Model):
    _name = 'fsc.audit.line'
    _description = 'FSC audit line'


    name = fields.Char('Name' , related='material_id.alias')
    fsc_audit_id = fields.Many2one('fsc.audit', string='FSC Audit', ondelete='cascade')

    material_id = fields.Many2one('product.material', string='Material')
    fsc_audit_product_ids = fields.One2many('fsc.audit.product', 'fsc_audit_line_id',
                                            string='Products', help='Products details')

    stock_start_vol = fields.Float('Start stock')
    stock_final_vol = fields.Float('Final stock')

    purchase_vol = fields.Float('Purchase volume')
    sale_vol = fields.Float('Sold')
    efficiency = fields.Float('Efficiency')
    is_hidden = fields.Boolean('Hidden') # Falta compute (sin volumen de compra o stock inicial)
