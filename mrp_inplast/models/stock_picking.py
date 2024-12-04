from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = "stock.picking"

    def add_sscc(self):
        partner = self.partner_id or self.parent_id.partner_id  # Obtener el partner
        for line in self.move_line_ids:
            for sscc in range(partner.sscc_qty):
                line.lot_id.get_next_sscc()
        return True

    @api.depends('move_line_ids','partner_id.mrp_bom_template_ids')
    def _get_not_allowed_partner_packaging(self):
        for record in self:
            allowed = False
            for sm in record.move_ids_without_package:
                for sml in sm.move_line_ids:
                    bom_template = self.env['stock.move.line'].search(
                        [('lot_id', '=', sml.lot_id.id), ('product_id', '=', sm.product_id.id)]).mrp_bom_template_id
                    if (bom_template.id) and (record.partner_id.mrp_bom_template_ids.ids) and (
                            bom_template.id not in record.partner_id.mrp_bom_template_ids.ids):
                        allowed = True
            record['incompatible_bom_template'] = allowed
    incompatible_bom_template = fields.Boolean('Incompatible packaging', store=True, compute='_get_not_allowed_partner_packaging')

    @api.constrains('state')
    def _not_allowed_partner_packaging_constrains(self):
        if self.state == 'done' and self.incompatible_bom_template == True:
            raise UserError('Incompatible packaging format for this customer. Review and reserve manually.')