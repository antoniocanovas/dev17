# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    # PARA TERRITORIO ESPAÑOL:
    @api.depends('country_id', 'state_id')
    def _get_ipnr_tax_zone(self):
        for record in self:
            record.ipnr_tax_zone = record.country_id.code == 'ES'
    ipnr_tax_zone = fields.Boolean('IPNR tax zone', store=True, compute='_get_ipnr_tax_zone')

    # PARA TERRITORIO ESPAÑOL, régimen DUA (Canarias/Ceuta-Melilla):
    @api.depends('country_id', 'state_id')
    def _get_ipnr_dua_tax_zone(self):
        for record in self:
            record.ipnr_dua_tax_zone = (
                record.country_id.code == 'ES'
                and bool(record.state_id)
                and record.state_id.code in ['GC', 'TF']
            )
    ipnr_dua_tax_zone = fields.Boolean('IPNR DUA tax zone', store=True, compute='_get_ipnr_dua_tax_zone')
