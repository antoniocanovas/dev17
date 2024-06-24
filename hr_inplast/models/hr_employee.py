
from odoo import api, fields, models



class PrivateInformation(models.Model):
    _inherit = "hr.employee"

    discapacity = fields.Float("Discapacity")
    locker = fields.Char("Locker")
    note = fields.Text("Notes")
    medical_control = fields.Date("Medical Control")
    emergency_plan_id = fields.Many2one("emergency.plan", string="Emergeny Plan")


