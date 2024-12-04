from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def add_sscc(self):
        partner = self.partner_id or self.parent_id.partner_id  # Obtener el partner

        for line in self.move_line_ids:
            for sscc in range(partner.sscc_qty):

                line.lot_id.get_next_sscc()

        return True
