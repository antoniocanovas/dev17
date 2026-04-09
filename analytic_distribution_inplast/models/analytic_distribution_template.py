from odoo import fields, models, api
from odoo.exceptions import UserError


class AnalyticDistributionTemple(models.Model):
    _inherit = "analytic.distribution.template"

    compute_method = fields.Selection(selection_add=
        [
            ("r1", "R1.- Descarga y ubicación de asas"),
            ("r2", "R2.- Recogida de palet y ubicación"),
            ("r3", "R3.- Carga contenedor"),
            ("r3.1", "R3.1.- Desubicación y carga"),
            ("r4", "R4.- Recepción y pesaje de materiales"),
            ("r5", "R5.- Aprovisionamiento materiales producción"),
            ("r6", "R6.- Coste almacenamiento MP"),
            ("r7", "R7.- Coste almacenamiento producto"),
            ("r8", "R8.- Materia prima (plástico, colorantes y aditivos)"),
            ("r9", "R9.- Materia prima 2 (cajas, palets y envoltorios)"),
            ("r10", "R10.- Gastos personal 1"),
            ("r10_legacy", "R10 Legacy.- Gastos personal 1 (Legacy)"),
            ("r11", "R11.- Gastos personal 2"),
            ("r11_legacy", "R11 Legacy.- Gastos personal 2 (Legacy)"),
            ("r12", "R12.- Amortizaciones de maquinaria y utillajes"),
            ("r12_legacy", "R12 Legacy.- Amortizaciones de maquinaria y utillajes (Legacy)"),
            ("r13", "R13.- Electricidad"),
            ("r13_legacy", "R13 Legacy.- Electricidad (Legacy)"),
            ("r14", "R14.- Calidad 1"),
            ("r14_legacy", "R14 Legacy.- Calidad 1 (Legacy)"),
            ("r15", "R15.- Calidad 2"),
            ("r15_legacy", "R15 Legacy.- Calidad 2 (Legacy)"),
            ("r16", "R16.- Servicios de TALLER"),
            ("r16_legacy", "R16 Legacy.- Servicios de TALLER (Legacy)"),
            ("r16.1", "R16.1.- Servicios de MANTENIMIENTO"),
            ("r16.1_legacy", "R16.1 Legacy.- Servicios de MANTENIMIENTO (Legacy)"),
            ("r17", "R17.- Costes de repaciones de máquinas, moldes y otros"),
            ("r17_legacy", "R17.- Costes de repaciones de máquinas, moldes y otros (legacy)"),
            ("r18", "R18.- Gastos planificación MRP"),
            ("r18.1", "R18.- Gastos planificación ASAS"),
            ("r19", "R19.- Gestión pedidos clientes por palets del albarán"),
            ("r20", "R20.- Gastos gestión pedidos de venta"),
            ("r21", "R21.- Planificación y registro producción"),
            ("r22", "R22.- Comercial por zona geográfica"),
            ("r23", "R23.- Generales por tipo de producto"),
        ]
    )

    workcenter_ids = fields.Many2many("mrp.workcenter", string="Workcenters")


    # 10/feb esto sobra, que se elimine tras validar con Alex que irá a través de planes analíticos generales:
    def _get_analytic_distribution_plan(self):
        self.analytic_distribution_plan_id = self.env.company.analytic_distribution_plan_id.id
    analytic_distribution_plan_id = fields.Many2one('account.analytic.plan', string='Distribution plan',
                                                    compute='_get_analytic_distribution_plan')

