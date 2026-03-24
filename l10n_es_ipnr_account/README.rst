=====================
IPNR - Facturación
=====================

.. |badge1| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta
.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1| |badge2|

Gestión del **Impuesto especial sobre los envases de plástico no reutilizables (IPNR)**
en facturas de Odoo, regulado por el **Real Decreto 1055/2022** y la
**Ley 7/2022 de residuos y suelos contaminados**.

El módulo automatiza el cálculo de la aportación IPNR, la generación del apunte
contable asociado y el control de su obligatoriedad al confirmar facturas de venta
y de compra.

**Table of contents**

.. contents::
   :local:

Normativa aplicable
===================

* **Ley 7/2022**, de 8 de abril, de residuos y suelos contaminados para una economía
  circular.
* **Real Decreto 1055/2022**, de 27 de diciembre, de envases y residuos de envases.

Son sujetos pasivos del impuesto los **fabricantes** (*manufacturer*) y los
**adquirentes intracomunitarios o importadores** (*acquirer*) de envases de plástico
no reutilizables. El ámbito territorial es el **territorio español** (excluidas
Canarias, Ceuta y Melilla, que aplican régimen DUA).

Configuración
=============

Compañía
--------

Acceder a **Facturación > Configuración > Compañías** y, en la pestaña **IPNR**:

* **Habilitar IPNR**: activa el módulo para esa compañía.
* **IPNR fecha desde**: fecha mínima a partir de la que se aplica el impuesto
  (obligatorio cuando IPNR está habilitado).
* **Diario de apuntes IPNR**: diario contable en el que se crearán los apuntes
  del impuesto.
* **Cuenta adquirente**: cuenta contable para operaciones de adquisición.
* **Cuenta fabricante**: cuenta contable para operaciones de fabricación.
* **Validación automática en compras / ventas**: si está activa, el apunte IPNR
  se confirma automáticamente al validar la factura.
* **Consolidar líneas IPNR**: agrupa las líneas de contribución en una sola al
  facturar desde múltiples pedidos.
* **Mostrar cantidades IPNR en informes**: incluye el importe IPNR desglosado en
  los informes de factura.

Tarifa IPNR
-----------

La tarifa aplicable se configura en **Facturación > Configuración > Tarifa IPNR**.
Cada registro define un rango de fechas y un precio (€/kg). Si el campo
*Fecha hasta* queda vacío, la tarifa estará vigente indefinidamente desde la
*Fecha desde*. Los rangos no pueden solaparse.

La tarifa predeterminada es **0,45 €/kg** desde el 27/12/2022.

Posición fiscal
---------------

En **Facturación > Configuración > Posiciones Fiscales**, marcar la casilla
**Sujeto a IPNR** en las posiciones fiscales bajo las que aplica el impuesto.
Las posiciones fiscales con esta opción desmarcada excluyen la operación del IPNR
aunque el producto esté sujeto.

Productos
---------

En la ficha de cada producto, campo **Sujeto a IPNR**:

* **Categoría**: hereda la configuración de la categoría del producto.
* **Sí**: siempre sujeto, independientemente de la categoría.
* **No**: nunca sujeto, independientemente de la categoría.

Adicionalmente:

* **Tipo de plástico**: *Fabricante* o *Adquirente*, según el rol de la empresa
  respecto a ese envase.
* **Peso de plástico no reciclable (kg)**: peso que se usa como base imponible
  para el cálculo del impuesto.

Categorías de producto
----------------------

En la configuración de la categoría se puede marcar **Sujeto a IPNR** para que
todos los productos de esa categoría con la opción «Categoría» hereden la sujeción.

Partners
--------

El campo **Zona IPNR** del partner se calcula automáticamente:

* **Zona IPNR**: ``True`` si el país del partner es España.
* **Zona DUA**: ``True`` si es España y la provincia es Canarias (GC/TF).

Uso
===

Campo ``is_ipnr`` en líneas de factura
---------------------------------------

Cada línea de factura tiene el campo ``is_ipnr``, que determina si esa línea está
sujeta al impuesto. Se calcula automáticamente considerando:

* El producto tiene ``ipnr_subject`` = «Sí» o «Categoría» (con categoría marcada).
* El tipo de plástico del producto es «Fabricante» o «Adquirente».
* El partner de envío (facturas de venta) o el partner de la compañía (facturas
  de compra) está en zona IPNR (territorio español continental).

El campo es editable para permitir ajustes manuales.

Facturas de venta
-----------------

Al añadir líneas con productos IPNR, el módulo:

1. Crea automáticamente una línea de **Aportación IPNR** con el peso total y la
   tarifa vigente en la fecha de factura.
2. Muestra un **aviso informativo** en la cabecera si la operación requiere crear
   el apunte contable IPNR.
3. Muestra el **botón «Plastic Tax entry»** para crear el apunte manualmente en
   borrador y revisarlo antes de confirmar.
4. **Bloquea la validación** de la factura si no existe apunte IPNR asociado y la
   operación lo requiere.

El botón y el aviso aparecen cuando se cumplen simultáneamente:

* La compañía tiene IPNR habilitado.
* El partner de envío está en zona IPNR.
* La posición fiscal está marcada como sujeta a IPNR (o no hay posición fiscal).
* Existe al menos una línea ``is_ipnr = True`` con cantidad distinta de cero.

Facturas de compra
------------------

Las facturas de compra **no generan líneas de aportación IPNR automáticamente**,
ya que se asume que vienen del pedido de compra o se crean manualmente.

El **botón «Plastic Tax entry»** es visible cuando la compañía tiene IPNR
habilitado y hay al menos una línea ``is_ipnr = True`` con cantidad distinta de
cero.

Al pulsar el botón, el apunte contable se genera según la siguiente prioridad:

1. Si la factura contiene líneas del producto **Aportación IPNR** (incluidas desde
   el pedido de compra o manualmente), se usa el importe directo de esas líneas
   (cantidad × precio unitario).
2. Si no hay líneas de contribución, se calcula desde las líneas ``is_ipnr = True``
   aplicando la fórmula ``cantidad × peso_no_reciclable × tarifa_IPNR``.

**Actualización automática del apunte en borrador**: si se cambia el proveedor o
las cantidades de una factura de compra en borrador que ya tiene apunte IPNR en
borrador, el apunte se actualiza automáticamente (partner e importes). Si el cambio
hace que ya no aplique IPNR, el apunte queda sin líneas (importe 0).

Apunte contable (Plastic Tax Entry)
-------------------------------------

El apunte se crea en el diario IPNR configurado en la compañía con la siguiente
asignación de cuentas según tipo de operación:

+---------------------+----------+-------------+-----------+------------------+
| Tipo factura        | Zona     | Tipo prod.  | Debe      | Haber            |
+=====================+==========+=============+===========+==================+
| Venta               | Sí       | Fabricante  | Ing. vta. | Cta. fabricante  |
+---------------------+----------+-------------+-----------+------------------+
| Venta               | Sí       | Adquirente  | Ing. vta. | Cta. adquirente  |
+---------------------+----------+-------------+-----------+------------------+
| Venta               | No       | Adquirente  | Cta. adq. | Ing. vta.        |
+---------------------+----------+-------------+-----------+------------------+
| Rectif. venta       | Sí       | Fabricante  | Cta. fab. | Ing. vta.        |
+---------------------+----------+-------------+-----------+------------------+
| Rectif. venta       | Sí       | Adquirente  | Cta. adq. | Ing. vta.        |
+---------------------+----------+-------------+-----------+------------------+
| Compra              | Sí       | —           | Gasto     | Cta. adquirente  |
+---------------------+----------+-------------+-----------+------------------+
| Rectif. compra      | Sí       | —           | Cta. adq. | Gasto            |
+---------------------+----------+-------------+-----------+------------------+

Ciclo de vida del apunte
~~~~~~~~~~~~~~~~~~~~~~~~

* Al **confirmar** la factura, si la compañía tiene configurada la validación
  automática, el apunte IPNR se confirma también.
* Al **pasar a borrador** la factura, el apunte IPNR vuelve a borrador si estaba
  confirmado.
* Al **cancelar** la factura, el apunte IPNR vuelve a borrador si estaba
  confirmado.

Alerta por peso no configurado
-------------------------------

Si al calcular la aportación IPNR algún producto sujeto no tiene el campo
*Peso de plástico no reciclable* relleno, se crea una **actividad de aviso**
(tipo «Warning») en la factura para notificar al usuario.

Known issues / Roadmap
======================

* Las facturas generadas desde pedidos de comercio electrónico no reciben
  tratamiento especial adicional.
* La actualización automática del apunte IPNR en borrador solo se realiza para
  facturas de compra; en ventas el apunte debe recrearse manualmente si cambian
  los datos.

Bug Tracker
===========

Para reportar incidencias o sugerencias, contactar con el equipo de desarrollo.

Credits
=======

Authors
~~~~~~~

* Pedro Guirao
* Antonio Cánovas

Contributors
~~~~~~~~~~~~

* Manuel Regidor <manuel.regidor@sygel.es>
* Pedro Guirao
* Antonio Cánovas
