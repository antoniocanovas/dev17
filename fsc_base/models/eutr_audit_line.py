# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api

class EutrAuditLine(models.Model):
    _name = 'eutr.audit.line'
    _description = 'EUTR audit line'


    product_id = fields.Many2one('product.product', string='Product')
    name = fields.Char('Name' , related='product_id.material_id.alias')
    eutr_audit_id = fields.Many2one('eutr.audit', string='EUTR Audit', ondelete='cascade')

    intrastat_code_id = fields.Many2one(related='product_id.intrastat_code_id', string='Intrastat')
    eutr_nc_code = fields.Char('NC', related='product_id.eutr_nc_code')
    volume = fields.Float('Quantity (TM)')
    state_id = fields.Many2one('res.country.state', string='State')
    country_id = fields.Many2one(related='state_id.country_id')
    eutr_cdc = fields.Boolean('CDC', help='FSC Custody chain')
    eutr_cl  = fields.Boolean('CL', help='Legal control')