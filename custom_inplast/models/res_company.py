# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api


class ResCompany(models.Model):
    _inherit = "res.company"

    default_location_id = fields.Many2one(
        "stock.location",
        string="Ubicación migración",
        help="Ubicación de stock que se utilizará en la función mig_inventario"
        " para la migración de inventarios. "
        "Esta ubicación determina dónde se crearán los movimientos de stock durante"
        " el proceso de migración.",
    )

    default_location_dest_id = fields.Many2one(
        "stock.location",
        string="Ubicación destino migración",
        help="Ubicación de destino para los traslados internos generados durante "
        "la migración de inventarios. "
        "Se creará un albarán de traslado interno desde la ubicación de migración "
        "hacia esta ubicación.",
    )

    use_new_migration_logic = fields.Boolean(
        string="Usar nueva lógica de migración",
        default=False,
        help="Si está marcado, se utilizará la nueva lógica de migración "
        "que incluye validaciones de configuración, creación de paquetes SSCC "
        "y aplicación de reglas de putaway.",
    )

    def calcular_digito_verificador(self, numero):
        # Invertir el número para empezar desde el final
        numero = numero[::-1]

        suma = 0
        # Aplicar las multiplicaciones de 3 y 1 alternadas
        for i, digito in enumerate(numero):
            digito = int(digito)
            if i % 2 == 0:
                suma += digito * 3
            else:
                suma += digito * 1

        # Calcular el dígito verificador
        siguiente_decena = (suma + 9) // 10 * 10
        digito_verificador = siguiente_decena - suma

        return digito_verificador

    def generar_sscc(self, digito_extension, numero_identificacion_empresa, numero_serie):
        # Concatenar los componentes del SSCC
        base_sscc = f"{digito_extension}{numero_identificacion_empresa}{numero_serie}"

        # Calcular el dígito verificador
        digito_verificador = self.calcular_digito_verificador(base_sscc)

        # Formar el SSCC completo
        sscc_completo = f"{base_sscc}{digito_verificador}"

        return sscc_completo

    # Ejemplo de uso
#    digito_extension = "0"
#    numero_identificacion_empresa = "123456789"
#    numero_serie = "000000123456"

#    sscc = generar_sscc(self, digito_extension, numero_identificacion_empresa, numero_serie)
#    print("El SSCC es:", sscc)