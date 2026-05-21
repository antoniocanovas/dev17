# Stock Picking Invoicing — Extensiones Inplast

Módulo propio que extiende [`stock_picking_invoicing`](https://github.com/OCA/account-invoicing) (OCA)
sin modificar su código fuente. Contiene correcciones de comportamiento y nuevas funcionalidades
adaptadas a la operativa de Inplast.

---

## Dependencias

| Módulo | Origen |
|---|---|
| `stock_picking_invoicing` | OCA / account-invoicing |

---

## Funcionalidades

### 1. Corrección de facturación en albaranes de dropshipping

**Problema en el módulo OCA:**

El wizard `stock.invoice.onshipping` determina el tipo de diario contable y el tipo de
factura mirando únicamente el código del tipo de operación y la ubicación de **origen** del
albarán. Para el caso de dropshipping —albarán `incoming` con origen en proveedor
(`supplier`) y destino en cliente (`customer`)— el módulo OCA:

- Selecciona diario de **compra** en lugar de venta.
- No tiene entrada explícita en `INVOICE_TYPE_MAP` para esta combinación, recayendo en el
  valor por defecto `out_invoice` de forma accidental.

El resultado es un wizard que muestra "Create Supplier Invoice" y usa el diario de compras
para lo que debería ser una factura de venta al cliente.

**Solución aplicada** (`wizards/stock_invoice_onshipping.py`):

Se heredan los métodos `_get_journal_type` y `_get_invoice_type` del wizard. Cuando se
detecta el patrón de dropshipping —`incoming`, origen `supplier`, destino `customer`— se
devuelven `"sale"` y `"out_invoice"` respectivamente, antes de llamar al `super()`.

La detección del patrón se realiza en la función auxiliar `_is_dropship(picking)` que
comprueba los tres valores:

```
picking_type_id.code == "incoming"
location_id.usage    == "supplier"
location_dest_id.usage == "customer"
```

---

### 2. Acción contextual: Marcar para facturar y crear facturas borrador

**Necesidad:**

El flujo estándar del módulo OCA requiere dos pasos manuales: primero marcar cada albarán
como *Para Facturar* y luego abrir el wizard de facturación. Con selecciones de múltiples
albaranes esto es repetitivo.

**Solución implementada:**

Se añade una acción de servidor vinculada al modelo `stock.picking` que aparece en el
menú **Acción** al seleccionar uno o varios albaranes en la vista de lista:

> **Marcar para facturar y crear facturas borrador**

La acción ejecuta `stock.picking.action_mark_and_invoice()` con los registros seleccionados
y realiza en un único paso:

| Paso | Detalle |
|---|---|
| **Filtrado** | Solo albaranes en estado `done` y con `invoice_state != 'invoiced'`. Los ya facturados se ignoran silenciosamente. |
| **Marcado** | Llama a `set_to_be_invoiced()` sobre todos los válidos. Es idempotente: si alguno ya estaba marcado como `2binvoiced`, no hay efecto negativo. |
| **Generación** | Instancia `stock.invoice.onshipping` con los albaranes en contexto (`active_ids`) y llama a `_action_generate_invoices()`. Se reutiliza toda la lógica del wizard OCA (agrupación por albarán, detección de tipo de factura, diario contable). |
| **Estado** | Actualiza `invoice_state` a `invoiced` en los albaranes cuya factura se ha creado. |
| **Redirección** | Abre automáticamente la vista de las facturas borrador generadas (lista si son varias, formulario si es una sola). |

**Parámetros de facturación usados por defecto:**

- Agrupación: una factura por albarán (`group = "picking"`).
- Fecha de factura: fecha actual.
- Diario: el primero disponible del tipo que corresponda (venta o compra), según la lógica
  del wizard OCA extendida con el fix de dropshipping descrito en el punto anterior.

**Comportamiento con selecciones heterogéneas:**

Si se seleccionan albaranes de distinto tipo (p. ej. entregas a cliente y recepciones de
proveedor), el tipo de factura y el diario se determinan a partir del **primer albarán** del
conjunto, lo que es una limitación del diseño actual del wizard OCA. En la práctica, se
recomienda seleccionar albaranes del mismo tipo operativo.

---

## Instalación

```bash
odoo -u stock_picking_invoicing_inplast -d <base_de_datos>
```

No requiere migración de datos ni cambios en la base de datos.

---

## Archivos del módulo

```
stock_picking_invoicing_inplast/
├── __init__.py
├── __manifest__.py
├── README.md
├── data/
│   └── action_mark_and_invoice.xml     # Acción de servidor contextual
├── models/
│   └── stock_picking.py                # action_mark_and_invoice()
└── wizards/
    └── stock_invoice_onshipping.py     # Fix dropshipping
```
