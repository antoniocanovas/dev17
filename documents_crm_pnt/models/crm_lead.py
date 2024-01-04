# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api, _
from odoo.exceptions import UserError

class CrmLead(models.Model):
    _inherit = "crm.lead"


    document_count = fields.Integer('Document Count', related='partner_id.document_count')

    def action_see_documents(self):
        self.ensure_one()
        return {
            'name': _('Documents'),
            'domain': [('partner_id', '=', self.partner_id.id)],
            'res_model': 'documents.document',
            'type': 'ir.actions.act_window',
            'views': [(False, 'kanban')],
            'view_mode': 'kanban',
            'context': {
                "default_partner_id": self.partner_id.id,
                "searchpanel_default_folder_id": False
            },
        }