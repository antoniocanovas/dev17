import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ProductCategory(models.Model):
    _inherit = "product.category"

    #    pnt_pricelist_weight = fields.Float('Pricelist weight', store=True, copy=True)

    type = fields.Selection(
        [
            ("raw_cistern", "Raw Cistern"),
            ("raw_sack", "Raw Sack"),
            ("raw_pallet", "Raw Pallet"),
            ("raw_bag", "Raw Bags"),
            ("raw_cardboard", "Raw Cardboard"),
            ("raw_color", "Raw Color"),
            ("cap_mrp", "Cap MRP"),
            ("cap_distribution", "Cap Distribution"),
            ("handle", "Handle"),
            ("other", "Other"),
        ],
        string="Type",
        required=True,
        help="Select the type of parameter.",
    )

    pnt_code = fields.Char("Code")
    pnt_tolerance = fields.Float(
        "Tolerance", digits=(16, 2), help="Tolerance value (e.g., +/- 0.02)"
    )
