from odoo import _, api, fields, models

class ProjectProject(models.Model):
    _inherit = 'project.project'

    # Carpeta para Onedrive / Drive / Synology:
    pnt_cloudfolder = fields.Char('Cloud folder', store=True, copy=False, tracking=100,
                                  help='Folder link to other systems like Google Drive or Onedrive')
    # Texto para indicar nuevas carpetas a crear en Odoo documents, separadas por coma.
    pnt_documents_folders = fields.Char('New folders', store=True, copy=True, tracking=100,
                                        help='Any word or phrase written will be created as folder in project documents. \n'
                                             'You can write several folders separated by comma. \n'
                                             'This system does not delete the existing folder, you can remove the text. \n'
                                             'Permissions will be the same as the main project folder.')

    @api.onchange('pnt_documents_folders','documents_folder_id')
    def create_new_documents_folders(self):
        for record in self:
            temp_folders = []
            if (record.pnt_documents_folders) and (record.documents_folder_id.id):
                folders = record.pnt_documents_folders.split(",")

                # Quitar espacios iniciales y ordenar alfabéticamente para evitar errores en asignación "parent":
                for folder in folders:
                    temp_folders.append(folder.lstrip())
                folders = temp_folders.sorted()

                # Recorrer carpetas y subcarpetas, ya ordenadas:
                for fo in folders:
                    parent = record.documents_folder_id
                    subfolders = fo.split("/")
                    for subfo in subfolders:
                        name = subfo.lstrip()
                        exist = self.env['documents.folder'].search(
                            [('name', '=', name), ('parent_folder_id', '=', parent.id)])

                        # Podemos hacer esto, gracias al orden alfabético previo:
                        if exist.ids:
                            parent = exist[0]
                        else:
                            newfold = self.env['documents.folder'].create({
                                'name': name,
                                'parent_folder_id': parent.id,
                                'group_ids': parent.group_ids,
                                'read_group_ids': parent.read_group_ids,
                                'company_id': record.company_id.id,
                            })
                            parent = newfold
