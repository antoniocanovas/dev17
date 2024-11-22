# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.tools import sql


def pre_init_hook(env):
    if not sql.column_exists(env.cr, "account_move", "is_ipnr"):
        sql.create_column(env.cr, "account_move", "is_ipnr", "boolean")
    if not sql.column_exists(env.cr, "account_move", "ipnr_is_date"):
        sql.create_column(env.cr, "account_move", "ipnr_is_date", "boolean")
    if not sql.column_exists(env.cr, "product_product", "ipnr_has_amount"):
        sql.create_column(env.cr, "product_product", "ipnr_has_amount", "boolean")
