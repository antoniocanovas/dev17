# Módulo de Deconstrucción Automática para Palets (Inplast)

Este módulo extiende la funcionalidad del módulo `mrp_autounbuild` para proporcionar una lógica de deconstrucción personalizada y específica para los productos de tipo "palet" utilizados en el flujo de Inplast.

## Propósito

El objetivo es anular el comportamiento estándar de deconstrucción de Odoo (que se basa en explotar la lista de materiales completa) y reemplazarlo por un proceso a medida cuando se deconstruye un palet.

El resultado deseado de la deconstrucción de un palet es:
- **Consumo**: Se consume el producto "palet" que se está deconstruyendo.
- **Producción**:
    1. Se genera el producto "material de palet" (ej. el palet de madera físico), según la cantidad y el producto especificados en la línea de la LdM referenciada en el campo `pallet_line_id`.
    2. Se generan los productos contenidos en el palet (ej. cajas), basándose en los números de serie especificados en el campo `related_boxes_ids` del lote del palet. Se producirá una unidad por cada lote relacionado.

## Funcionalidades Clave

- **Anulación de `action_unbuild`**: El módulo intercepta la acción de deconstruir para comprobar si el producto es un "palet de Inplast".
- **Lógica Personalizada**: Si se cumple la condición, se ejecuta una función que crea manualmente los movimientos de stock necesarios para reflejar el resultado deseado, ignorando la LdM estándar.
- **Trazabilidad Completa**: El proceso maneja correctamente los productos con trazabilidad por lote/número de serie, tanto para el consumo del palet principal como para la producción de los componentes y el material del palet.

## Dependencias

Este módulo depende de:
- `mrp_autounbuild`: Hereda la funcionalidad base de deconstrucción.
- Otros módulos personalizados de Inplast que proveen los siguientes campos:
    - En `product.product`: `pnt_product_type`.
    - En `mrp.bom.template`: `type`.
    - En `mrp.bom`: `pallet_line_id`.
    - En `stock.lot`: `related_boxes_ids`.

## Configuración

Para que la deconstrucción personalizada funcione, se requiere la siguiente configuración:

### 1. Configuración del Producto

El producto que representa el palet a deconstruir debe tener:
- **Tipo de Producto (Inplast)** (`pnt_product_type`): `packing`.
- **Plantilla de LdM** (`mrp_bom_template_id`): Debe estar asociada a una plantilla cuyo `type` contenga la palabra `pallet`.

### 2. Configuración de la Lista de Materiales (LdM)

La LdM asociada al producto palet debe tener:
- **Línea de Palet** (`pallet_line_id`): Este campo debe apuntar a la línea de la LdM que contiene el producto "material de palet" y la cantidad que se devolverá al stock.

### 3. Configuración del Lote/Número de Serie

El lote (`stock.lot`) del palet que se va a deconstruir debe tener:
- **Lotes Relacionados** (`related_boxes_ids`): Este campo debe contener la lista de todos los lotes/números de serie de los productos (cajas) que están dentro del palet.

## Uso

1. Ir al menú de Inventario y seleccionar la operación de Deconstrucción.
2. Crear una nueva orden de deconstrucción.
3. Seleccionar el producto "palet" y el lote/número de serie correspondiente que se desea deconstruir.
4. Al confirmar la orden, el módulo detectará que es un palet de Inplast y ejecutará la lógica personalizada.
5. Los movimientos de stock resultantes reflejarán el consumo del palet y la producción del material del palet y las cajas contenidas.
