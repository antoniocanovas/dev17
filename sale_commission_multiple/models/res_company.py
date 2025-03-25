# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    customer_referrer_unique = fields.Boolean('Referrer unique', default=True,
                                              help='Unique referrer for all company sites and delegations.')
