from odoo import models, fields

class EmergencyPlan(models.Model):
    _name = 'emergency.plan'
    _description = 'Emergency Plan'

    pnt_name = fields.Char(string="Plan Name", required=True)
    pnt_description = fields.Text(string="Description")
    pnt_procedure = fields.Text(string="Procedure")
    pnt_contact_information = fields.Text(string="Contact Information")
    pnt_responsible_employee_id = fields.Many2one('hr.employee', string="Responsible Employee")
