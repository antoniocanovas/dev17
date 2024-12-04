from odoo import _, api, fields, models

class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _get_mrp_bom_template(self):
        for record in self:
            bomtemplate = False
            mrpproduction = self.env['mrp.production'].search([('name', '=', record.origin)])
            if mrpproduction.id:
                bomtemplate = mrpproduction[0].bom_id.mrp_bom_template_id.id
            record['mrp_bom_template_id'] = bomtemplate
    mrp_bom_template_id = fields.Many2one("product.bom.template", compute='_get_mrp_bom_template')
