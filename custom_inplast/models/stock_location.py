# Copyright 2023 Serincloud SL - Ingenieriacloud.com

from odoo import fields, models, api


class StockLocation(models.Model):
    _inherit = "stock.location"


    # Campos de migración facilitados por el cliente, se pueden eliminar en un futuro:
    pnt_calle = fields.Char('Calle')
    pnt_modulo = fields.Char('Módulo')
    pnt_altura = fields.Char('Altura')
    pnt_posicion = fields.Char('Posición')
    pnt_tipopaquete = fields.Integer('Tipo paquete',
                                     help='Todos 0, menos un par que son para picos y no previstos, que cabe todo lo '
                                          'que digamos; masivos. Habitualmente no desubicamos, no es stock. '
                                          'Una caja abierta se volverá a meter en producción.')
    pnt_modocolocacion = fields.Integer('Modo colocación',
                                        help='Todos 0, menos 10 que son "2" aparentemente de granel o amontonados. '
                                             'Confirmado que son masivos, por ejemplo naves alquiladas. '
                                             'Los masivos estándar son PICOS, PENDIENTES, MUELLES Y CALLE.')
    pnt_huecostotales =  fields.Integer('Huecos totales',
                                        help='LOS PALETS QUE CABEN EN CADA HUECO: 1, LOS DE CALLE (19), '
                                             'Y LOS 999 QUE SON GRANEL. PONER A 0 ES UNA FORMA DE BLOQUEARLO, '
                                             'SON LOS PISOS DE ABAJO, EL HUECO EXISTE PERO NO LO ESTAMOS USANDO. ES OPCIONAL')
    pnt_ubicaciondisponible = fields.Boolean('Ubicación disponible',
                                             help='MANUALMENTE SE BLOQUEA EL HUECO. SE PUEDE BLOQUEAR CON O SIN MATERIAL, '
                                                  'SI SE BLOQUEA APARECE COMO STOCK, PERO NO SE PUEDE SACAR. SERÍA UNA ESPECIE '
                                                  'DE "RESERVADO". Se puede cambiar de ubicación, por ejemplo calidad.')
    pnt_zona = fields.Char('Zona',
                           help='Zona1 y zona2 (son la mayoría) pertenecen a A1 ZONA1.- PALETS NORMALES, '
                                'ZONA2.- PALETS CORREDERA (19) OTRAS ZONAS SON LAS DE MASIVO Y PICOS. A LA HORA '
                                'DE UBICAR, PREFERENCIAS EN ZONA1, ZONA2. PARA DAR PREFERENCIA.')
    pnt_udlog = fields.Integer('Ud log',
                               help='Todos los huecos que no tienen pared son los "1", "0" son los que están pegados '
                                    'a la pared y "2" antes eran cajas sueltas.A NIVEL DE CÓDIGO DE ARTÍCULO, '
                                    'HAY UN CAMPO EN LA FAMILIA QUE INDICA LA UNIDAD LOGÍSTICA. "Si es esta '
                                    'familia o esta, va por aquí". ASAS=> 0 y si no al 1 TAPONES => Siempre al 1, '
                                    'en otro caso muelle ...')