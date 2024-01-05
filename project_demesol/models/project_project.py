from odoo import _, api, fields, models

class ProjectProject(models.Model):
    _inherit = 'project.project'

    # Carpeta para Onedrive / Drive / Synology:
    pnt_cloudfolder = fields.Char('Cloud folder', store=True, copy=False, tracking=True,
                                  help='Folder link to other systems like Google Drive or Onedrive')
    # Texto para indicar nuevas carpetas a crear en Odoo documents, separadas por coma.
    pnt_documents_folders = fields.Char('New folders', store=True, copy=True, tracking=True,
                                        help='Any word or phrase written will be created as folder in project documents. \n'
                                             'You can write several folders separated by comma. \n.'
                                             'This system does not delete the existing folder, you can remove the text. \n'
                                             'Permissions will be the same as the main project folder.')

    @api.onchange('pnt_documents_folders','documents_folder_id')
    def create_new_documents_folders(self):
        for record in self:
            if (record.pnt_documents_folders) and (record.documents_folder_id.id):
                folders = record.pnt_documents_folders.split(",")
                for fo in folders:
                    name = fo.lstrip()
                    exist = self.env['documents.folder'].search(
                        [('name', '=', name), ('parent_folder_id', '=', record.documents_folder_id.id)])
                    if not exist.ids:
                        newfold = self.env['documents.folder'].create({
                            'name': name,
                            'parent_folder_id': record.documents_folder_id.id,
                            'group_ids': record.documents_folder_id.group_ids,
                            'read_group_ids': record.documents_folder_id.read_group_ids,
                            'company_id': record.company_id.id,
                             })