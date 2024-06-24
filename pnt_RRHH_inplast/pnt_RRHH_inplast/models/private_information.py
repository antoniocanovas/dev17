
from odoo import api, fields, models



class PrivateInformation(models.Model):
    _inherit = "hr.employee"

    pnt_discapacity = fields.Float("Discapacity")
    pnt_locker = fields.Char("Locker")
    pnt_note = fields.Text("Notes")
    pnt_medical_control = fields.Date("Medical Control")
    pnt_emergency_plan = fields.Many2one("emergency.plan", string="Emergeny Plan")


