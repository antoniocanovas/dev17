from odoo import _, api, fields, models

class ProjectProject(models.Model):
    _inherit = 'project.project'

    # Carpeta para Onedrive / Drive / Synology:
    pnt_cloudfolder = fields.Char('Cloud folder', store=True, copy=False)
    pnt_documents_folders = fields.Char('New folders', store=True, copy=True,
                                        placeholder='New folder names separated by commas ...')

    @api.depends('pnt_documents_folders')
    def create_new_documents_folders(self):
        for record in self:
            if (record.pnt_documents_folders) and (record.documents_folder_id.id):
                folders = record.pnt_documents_folders.split(",")
                for fo in folders:
                    name = fo.lstrip()
                    exist = env['documents.folder'].search(
                        [('name', '=', name), ('parent_folder_id', '=', record.documents_folder_id.id)])
                    if not exist.ids:
                        newfold = env['documents.folder'].create(
                            {'name': name, 'parent_folder_id': record.documents_folder_id.id})