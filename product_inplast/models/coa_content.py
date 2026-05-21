from odoo import fields, models


class PntCoaContent(models.Model):
    _name = "pnt.coa.content"
    _description = "COA Content per Language"

    # Relación con el modelo PntCoa
    coa_id = fields.Many2one(
        "pnt.coa", string="COA Reference", required=True, ondelete="cascade"
    )
    type = fields.Selection(related="coa_id.type", string="Type", store=True)
    language_code = fields.Char(string="Language Code", required=True)

    coa_body = fields.Image(string="COA Body", max_width=1920, max_height=1920)
    multicolor_body = fields.Image(
        string="Multicolor Body", max_width=1920, max_height=1920
    )
    components_body = fields.Image(
        string="Components Body", max_width=1920, max_height=1920
    )
    table_batch_certificate = fields.Image(
        string="Table Batch Certificate", max_width=1920, max_height=1920
    )

    print_multicolor = fields.Boolean(
        related="coa_id.print_multicolor", string="Multicolor print"
    )
    print_quality_meassure = fields.Boolean(
        related="coa_id.print_quality_meassure", string="Quality meassures"
    )
    print_components = fields.Boolean(
        related="coa_id.print_components", string="Components print"
    )
