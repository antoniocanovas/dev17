# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api


class ProductCategory(models.Model):
    _inherit = "hr.employee"


    # Campos de migración facilitados por el cliente, se pueden eliminar en un futuro:
    mig_cuenta_bancaria = fields.Char('mig_cuenta_bancaria')
    mig_fecha_alta = fields.Date('mig_fecha_alta')
    mig_tarjeta = fields.Char('mig_tarjeta')
