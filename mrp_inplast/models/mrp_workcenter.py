from odoo import fields, models

class ProductBomTemplate(models.Model):
    _inherit = "mrp.workcenter"

    power_kw = fields.Float("Electric power (kw)")
    analytic_hr_per_hour = fields.Float("Analytic hr per hour")
