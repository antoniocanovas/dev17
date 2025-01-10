from odoo import fields, models, api
from odoo.exceptions import UserError


class AnalyticDistribution(models.Model):
    _inherit = "analytic.distribution"

    compute_mode = fields.Selection(
        [
            ("demo", "demo INPLAST"),
            ("r13", "R13.- Electricidad"),
            ("r14", "R14.- Calidad"),
            ("r15", "R15.- Calidad"),
            ("r22", "R22.- Ventas por región y subfamilia"),
        ]
    )

    workcenter_ids = fields.Many2many("mrp.workcenter", string="Workcenters")

    def compute_distribution(self):
        """Extend this function with custom Inplast analytic compute modes"""
        super().compute_distribution()
        self.env["account.analytic.line"].search(
            [("analytic_distribution_id", "=", self.id)]
        ).unlink()
        self.inplast_computed_modes()

    def inplast_computed_modes(self):
        if self.compute_mode == "demo":
            raise UserError("ok")
        elif self.compute_mode == "r13":
            self.compute_r13()
        elif self.compute_mode in ["r14","r15"]:
            self.compute_r14()
        elif self.compute_mode == "r22":
            self.compute_r22()


    def compute_r13(self):
        datefrom = self.date_from
        dateto = self.date_to
        total_kwh = 0  # Total de kWh consumidos por todas las máquinas
        workcenters = self.workcenter_ids
        amount = self.amount  # El coste a distribuir

        # Wororders entre fechas:
        workorders = self.env["mrp.workorder"].search(
            [
                ("workcenter_id", "in", workcenters.ids),
                ("date_start", ">=", datefrom),
                ("date_start", "<=", dateto),
            ]
        )

        # Inicialización de listas simples
        mrpproducts = []
        product_total_kwh = []

        # Cálculo del total de kWh consumidos
        for wo in workorders:
            product = wo.product_id
            duration = wo.duration
            machine = wo.workcenter_id

            # Identificamos productos únicos y agregamos a la lista si no están
            if product not in mrpproducts:
                mrpproducts.append(product)
                product_total_kwh.append(0)  # Inicializamos su consumo total a 0

            # Calculamos el consumo de kWh
            kwh_consumed = duration * machine.power_kw
            total_kwh += kwh_consumed

            # Actualizamos el consumo total por producto
            product_index = mrpproducts.index(product)
            product_total_kwh[product_index] += kwh_consumed

        # Verificar si hay consumo total de kWh para evitar la división por cero
        if total_kwh == 0:
            raise UserError("No hay consumo de energía registrado.")

        # Crear entradas analíticas para cada producto
        for i in range(len(mrpproducts)):
            product = mrpproducts[i]
            product_kwh = product_total_kwh[i]

            machine_percentage = (product_kwh / total_kwh) * 100
            machine_cost = (amount * machine_percentage) / 100

            # Buscar la cuenta analítica para el producto base tapón, o crearla:
            analytic_product = product
            if product.pnt_product_type == 'packing':
                analytic_product = product.pnt_parent_id

            analytic_account = self.env['account.analytic.account'].search([
                ('product_id','=',analytic_product.id)
            ])
            if not analytic_account.id:
                analytic_account = self.env['account.analytic.account'].create({
                    'product_id': analytic_product.id,
                    'plan_id': self.env.company.analytic_product_plan_id.id,
                    'name': analytic_product.name,
                })


            self.env["account.analytic.line"].create(
                {
                    "name": f"Consumo {product.name}",
                    "amount": machine_cost,
                    "product_id": product.id,
                    "date": fields.Date.today(),
                    "analytic_distribution_id": self.id,
                    "account_id": analytic_account.id,
                }
            )

        return True

    def compute_r14(self):
        datefrom = self.date_from
        dateto = self.date_to
        total_duration = 0  # Total de kWh consumidos por todas las máquinas
        workcenters = self.workcenter_ids
        amount = self.amount  # El máximo coste a distribuir

        # Órdenes de manufactura consideradas entre fechas:
        workorders = self.env["mrp.workorder"].search(
            [
                ("workcenter_id", "in", workcenters.ids),
                ("date_start", ">=", datefrom),
                ("date_start", "<=", dateto),
            ]
        )

        # Inicialización de listas simples
        mrpproducts = []
        product_total_duration = []

        # Cálculo del total de kWh consumidos
        for wo in workorders:
            product = wo.product_id
            duration = wo.duration
            machine = wo.workcenter_id

            # Identificamos productos únicos y agregamos a la lista si no están
            if product not in mrpproducts:
                mrpproducts.append(product)
                product_total_duration.append(0)  # Inicializamos su consumo total a 0

            total_duration += duration

            # Actualizamos el consumo total por producto
            product_index = mrpproducts.index(product)
            product_total_duration[product_index] += duration

        # Verificar si hay consumo total de kWh para evitar la división por cero
        if total_duration == 0:
            raise UserError("No hay consumo de energía registrado.")

        # Crear entradas analíticas para cada producto
        for i in range(len(mrpproducts)):
            product = mrpproducts[i]
            product_kwh = product_total_duration[i]

            machine_percentage = (product_kwh / total_duration) * 100
            machine_cost = (amount * machine_percentage) / 100

            self.env["account.analytic.line"].create(
                {
                    "name": f"Consumo {product.name}",
                    "amount": machine_cost,
                    "product_id": product.id,
                    "date": fields.Date.today(),
                    "analytic_distribution_id": self.id,
                }
            )

        return True

    def compute_r22(self):
        # El chequeo de región es el siguiente: país = España (ES), o posición fiscal "intracomuntaria" (EU) y otros.
        # La parametrización está hecha:
        analytic_spain = self.env.company.analytic_spain_account_id.id
        analytic_eu= self.env.companyanalytic_eu_account_id.id
        analytic_noneu = self.env.company.analytic_non_eu_account_id.id
        amount = self.amount

        fiscal_position_eu_external_id = "account." + self.company.id + "_" + "fp_intra"
        partner_eu = self.env.ref(fiscal_position_eu_external_id)

        if not analytic_spain.id or not analytic_eu.id or not analytic_noneu.id:
            raise UserError('Go to company => Analytic parametrization and assign region accounts.')

        # Cálculo para España: Todos los account.move.line de las cuentas, cuyo partner.country_id es España.
        #  Es UE si la posición fiscal es partner_eu.id; el resto a "Resto del mundo".

        #  Se hace el porcentaje sobre el total de venta,
        #  Se crea array de familia que ha sido cada venta (por array de venta, familia),
        #  Si existe cuenta analítica para esta familia, se añade apunte contable, en otro caso se crea y después añade.

        # El array podría ser: [ 'region', 'familia' , 'importe']
        # Después calcular en base al array.
        return True