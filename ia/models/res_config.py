from odoo import fields, models, _


class ResConfigSettings(models.TransientModel):

    _inherit = "res.config.settings"

    api_key = fields.Char(
        string="API Key",
        help="Provide the API key here",
        config_parameter="odoo_chatgpt_connector.api_key",
    )
