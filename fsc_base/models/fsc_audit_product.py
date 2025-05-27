# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api

class FscAuditProduct(models.Model):
    _name = 'fsc.audit.product'
    _description = 'FSC audit product'


    name = fields.Char('Name' , compute='_get_name')
    # Relaciones para o2m e informe principal:
    fsc_audit_line_id = fields.Many2one('fsc.audit.line', string='Audit line', ondelete='cascade')
    material_id = fields.Many2one(related='fsc_audit_line_id.material_id')
    fsc_audit_id = fields.Many2one(related='fsc_audit_line_id.fsc_audit_id', string='FSC Audit')
    # DATOS a calcular y utilizar en fsc.audit.line:
    product_id = fields.Many2one('product.product', string='Product', help='Product')
    fsc_format_id = fields.Many2one(related='product_id.fsc_format_value_id', string='Group')
    volume = fields.Float('Volume')
    type = fields.Selection([
        ('stock_start','Stock start'),
        ('stock_final', 'Stock final'),
        ('sale','Sale'),
        ('purchase','Purchase'),
    ],
        string='Type',
    )

    def _get_name(self):
        for record in self:
            if record.product_id and record.type:
                record.name = record.product_id.name + " (" + record.type + ")"
