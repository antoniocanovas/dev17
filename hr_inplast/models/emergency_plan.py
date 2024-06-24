from odoo import models, fields

class EmergencyPlan(models.Model):
    _name = 'emergency.plan'
    _description = 'Emergency Plan'

    name = fields.Char(string="Plan Name", required=True)
    description = fields.Text(string="Description")
    procedure = fields.Text(string="Procedure")
    contact_information = fields.Text(string="Contact Information")
    responsible_employee_id = fields.Many2one('hr.employee', string="Responsible Employee")
