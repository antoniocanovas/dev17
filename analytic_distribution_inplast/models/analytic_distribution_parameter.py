# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models, api
from odoo.exceptions import UserError

class AnalyticDistributionParameter(models.Model):
    _name = 'analytic.distribution.parameter'
    _description = 'Analytic Distribution Parameters'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string='Name',
        required=True
    )

    # Warehouse (load/unload)
    truck_load = fields.Float(
        string='Truck load',
        help="Time required to load a truck."
    )
    container_load = fields.Float(
        string='Container load',
        help="Time required to load a container."
    )
    picking_unload = fields.Float(
        string='Picking unload',
        help="Time required to unload a picking slip (1h per slip)."
    )

    # Raw material reception (load/unload)
    raw_cistern_unload = fields.Float(
        string='Cistern unload',
        help="Time required to unload a cistern."
    )
    raw_sack_unload = fields.Float(
        string='Sack unload',
        help="Time required to unload sacks of raw material."
    )
    raw_color_unload = fields.Float(
        string='Color unload',
        help="Time required to unload color material."
    )
    raw_pallet_unload = fields.Float(
        string='Pallet unload',
        help="Time required to unload pallets."
    )
    raw_cardboard_unload = fields.Float(
        string='Cardboard unload',
        help="Time required to unload cardboard."
    )
    raw_bag_unload = fields.Float(
        string='Bag unload ',
        help="Time required to unload bags."
    )

    # Internal transfer to production
    raw_color_reloc_daily = fields.Float(
        string='Color',
        help="Daily internal relocation time for color (hours per day)."
    )
    raw_pallet_reloc_daily = fields.Float(
        string='Pallet ',
        help="Daily internal relocation time for pallets (hours per day)."
    )
    raw_cboard_reloc_daily = fields.Float(
        string='Cardboard',
        help="Daily internal relocation time for cardboard (hours per day)."
    )
    raw_bag_reloc_daily = fields.Float(
        string='Bag',
        help="Daily internal relocation time for bags (hours per day)."
    )

    # Other fields
    pallet_reloc = fields.Float(
        string='Minutes per pallet',
        help="Minutes required to relocate each pallet."
    )
    container_box_qty = fields.Integer(
        string='Boxes per container',
        help="Number of boxes that fit in a container."
    )
