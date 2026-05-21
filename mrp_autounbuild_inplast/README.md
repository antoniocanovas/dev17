# Módulo de Deconstrucción Automática para Palets (Inplast)

Este módulo extiende la funcionalidad del módulo `mrp_autounbuild` para proporcionar una lógica de deconstrucción personalizada y específica para los productos de tipo "palet" utilizados en el flujo de Inplast.

## Propósito

El objetivo es anular el comportamiento estándar de deconstrucción de Odoo (que se basa en explotar la lista de materiales completa) y reemplazarlo por un proceso a medida cuando se deconstruye un palet.

El resultado deseado de la deconstrucción de un palet es:
- **Consumo**: Se consume el producto "palet" que se está deconstruyendo.
- **Producción**:
    1. Se genera el producto "material de palet" (ej. el palet de madera físico), según la cantidad y el producto especificados en la línea de la LdM referenciada en el campo `pallet_line_id`.
    2. Se generan los productos contenidos en el palet (ej. cajas), mediante uno de estos dos mecanismos según el lote del palet:
        - **Con `related_boxes_ids`**: Se produce una unidad por cada lote relacionado encontrado en el campo `related_boxes_ids` del lote del palet.
        - **Sin `related_boxes_ids` (fallback por LdM)**: Se utiliza el componente caja definido en la LdM (`box_line_id`) con la cantidad indicada en la misma (`box_count`), asignando el mismo nombre de lote que el palet.

## Funcionalidades Clave

- **Anulación de `action_unbuild`**: El módulo intercepta la acción de deconstruir para comprobar si el producto es un "palet de Inplast".
- **Lógica Personalizada**: Si se cumple la condición, se ejecuta una función que crea manualmente los movimientos de stock necesarios para reflejar el resultado deseado, ignorando la LdM estándar.
- **Doble modo de producción de cajas**:
    - Si el lote tiene `related_boxes_ids`, se producen los componentes a partir de esos lotes relacionados.
    - Si el lote **no** tiene `related_boxes_ids`, se utiliza automáticamente la cantidad y el producto caja definidos en la LdM (`box_line_id` / `box_count`), creando o reutilizando un lote con el mismo nombre que el palet.
- **Trazabilidad Completa**: El proceso maneja correctamente los productos con trazabilidad por lote/número de serie, tanto para el consumo del palet principal como para la producción de los componentes y el material del palet.

## Dependencias

Este módulo depende de:
- `mrp_autounbuild`: Hereda la funcionalidad base de deconstrucción.
- Otros módulos personalizados de Inplast que proveen los siguientes campos:
    - En `product.product`: `pnt_product_type`.
    - En `mrp.bom.template`: `type`.
    - En `mrp.bom`: `pallet_line_id`, `box_line_id`, `box_count`.
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

El lote (`stock.lot`) del palet que se va a deconstruir puede tener:
- **Lotes Relacionados** (`related_boxes_ids`): Lista de lotes/números de serie de los productos (cajas) contenidos en el palet. Si está informado, se usa como base para generar los movimientos de componentes.
- Si este campo está **vacío**, el módulo recurre automáticamente al fallback por LdM: se toma el componente caja (`box_line_id`) y la cantidad (`box_count`) de la LdM, y se asigna el mismo nombre de lote que el palet. En este caso, la LdM debe tener correctamente configurada la línea de caja.

## Uso

1. Ir al menú de Inventario y seleccionar la operación de Deconstrucción.
2. Crear una nueva orden de deconstrucción.
3. Seleccionar el producto "palet" y el lote/número de serie correspondiente que se desea deconstruir.
4. Al confirmar la orden, el módulo detectará que es un palet de Inplast y ejecutará la lógica personalizada.
5. Los movimientos de stock resultantes reflejarán el consumo del palet y la producción del material del palet y las cajas contenidas.
