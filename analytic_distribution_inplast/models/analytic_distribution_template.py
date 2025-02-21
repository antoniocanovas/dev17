from odoo import fields, models, api
from odoo.exceptions import UserError


class AnalyticDistributionTemple(models.Model):
    _inherit = "analytic.distribution.template"

    compute_method = fields.Selection(selection_add=
        [
            ("r1", "R1.- Descarga y ubicación de asas (PDTE)"),
            ("r2", "R2.- Recogida de palet y ubicación (PDTE)"),
            ("r3", "R3.- Carga contenedor (PDTE)"),
            ("r3.1", "R3.1.- Desubicación y carga (PDTE)"),
            ("r4", "R4.- Recepción y pesaje de materiales (PDTE)"),
            ("r5", "R5.- Aprovisionamiento materiales producción (PDTE)"),
            ("r6", "R6.- Coste almacenamiento MP (PDTE)"),
            ("r7", "R7.- Coste almacenamiento producto (PDTE)"),
            ("r8", "R8.- Materia prima (PDTE)"),
            ("r9", "R9.- Materia prima 2 (PDTE)"),
            ("r10", "R10.- Gastos personal (PDTE)"),
            ("r11", "R11.- Gastos personal 2 (PDTE)"),
            ("r12", "R12.- Amortizaciones (PDTE)"),
            ("r13", "R13.- Electricidad"),
            ("r14", "R14.- Calidad (PDTE)"),
            ("r15", "R15.- Calidad 2 (PDTE)"),
            ("r16", "R16.- Gastos taller y mantenimiento (PDTE)"),
            ("r17", "R17.- Gastos taller y mantenimiento 2 (PDTE)"),
            ("r18", "R18.- Gastos planificación (PDTE)"),
            ("r19", "R19.- Gastos planificación 2 (PDTE)"),
            ("r20", "R20.- Gastos planificación 3 (PDTE)"),
            ("r21", "R21.- Gastos planificación 4 (PDTE)"),
            ("r22", "R22.- Comercial (PDTE)"),
            ("r23", "R23.- Generales (PDTE)"),
        ]
    )

    workcenter_ids = fields.Many2many("mrp.workcenter", string="Workcenters")


    # 10/feb esto sobra, que se elimine tras validar con Alex que irá a través de planes analíticos generales:
    def _get_analytic_distribution_plan(self):
        self.analytic_distribution_plan_id = self.env.company.analytic_distribution_plan_id.id
    analytic_distribution_plan_id = fields.Many2one('account.analytic.plan', string='Distribution plan',
                                                    compute='_get_analytic_distribution_plan')

