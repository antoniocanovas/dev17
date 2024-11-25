# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    # PARA TERRITORIO ESPAÑOL, EXCLUIR PROVINCIAS CON CODE = GC y TF, el código del tipo de envío es dropship
    @api.depends('country_id','state_id')
    def _get_ipnr_tax_zone(self):
        for record in self:
            taxzone = False
            if (record.country_id.code == 'ES') and (record.state_id.id) and (record.state_id.code not in ['GC','TF']):
                taxzone = True
            record['ipnr_tax_zone'] = taxzone
    ipnr_tax_zone = fields.Boolean('IPNR tax zone', store=True, compute='_get_ipnr_tax_zone')
