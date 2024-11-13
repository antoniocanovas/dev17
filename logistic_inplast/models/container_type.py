from odoo import _, api, fields, models

class ContainerType(models.Model):
    _name = "container.type"
    _description = "Container type"

    name = fields.Char("Name")
    type = fields.Selection(
        [
            ("truck", "Truck"),
            ("container", "Container"),
            ("plane", "Plane"),
        ],
        string="Type",
        required=True,
    )
    description = fields.Html('Description')
