# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    analytic_account_ids = fields.Many2many(
        'account.analytic.account',
        string='Analytic accounts',
        compute='_compute_analytic_account_ids',
        store=True
    )

    @api.depends('analytic_distribution')
    def _compute_analytic_account_ids(self):
        for line in self:
            analytic_ids = []
            if line.analytic_distribution:
                # Como analytic_distribution es un campo JSON,
                # se espera que line.analytic_distribution sea un diccionario
                # cuyas claves son cadenas con IDs separados por comas.
                for key in line.analytic_distribution.keys():
                    # Separamos la cadena por comas y convertimos cada parte en entero
                    ids = [int(x.strip()) for x in key.split(',') if x.strip().isdigit()]
                    analytic_ids.extend(ids)
            # Eliminamos duplicados y asignamos el Many2many
            line.analytic_account_ids = [(6, 0, list(set(analytic_ids)))]
