from odoo import _, api, fields, models
from odoo.exceptions import UserError

class ProductMaterial(models.Model):
    _inherit = 'product.material'

    wood_tracking = fields.Boolean('Wood Tracking')
    is_cites = fields.Boolean('Is CITES')
    type = fields.Selection(default='wood')