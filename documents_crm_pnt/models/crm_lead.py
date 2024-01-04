# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api, _
from odoo.exceptions import UserError

class CrmLead(models.Model):
    _inherit = "crm.lead"


    def _compute_document_count(self):
        read_group_var = self.env['documents.document']._read_group(
            [('partner_id', 'in', self.partner_id.ids)],
            groupby=['partner_id'],
            aggregates=['__count'])

        document_count_dict = {partner.id: count for partner, count in read_group_var}
        for record in self:
            record.document_count = document_count_dict.get(record.id, 0)
    document_count = fields.Integer('Document Count', compute='_compute_document_count')

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