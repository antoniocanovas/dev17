# Módulo de Productos Inplast

Este módulo extiende los modelos estándar de producto, categoría, ubicación de stock y albarán para cubrir las necesidades específicas de Inplast: clasificación MRP de productos, gestión del COA multilingüe, códigos de cliente por partner, etiquetado de almacén y automatización del empaquetado en palés.

---

## Clasificación de Productos (`product.template`)

### Tipo de producto (`pnt_product_type`)

Cada producto debe clasificarse obligatoriamente con uno de los siguientes tipos:

| Valor | Descripción |
|-------|-------------|
| `final` | Producto terminado |
| `semi` | Semielaborado |
| `packing` | Envase/embalaje |
| `raw` | Materia prima |
| `dye` | Colorante |
| `additive` | Aditivo |
| `packaging` | Packaging secundario |
| `box` | Caja |
| `pallet` | Palé |
| `tool` | Utillaje |
| `other` | Otros |

### Relaciones entre productos

- **`pnt_parent_id`**: Producto final o semielaborado al que pertenece este envase. Solo visible para tipos `semi` y `packing`; obligatorio para `packing`.
- **`pnt_parent_qty`**: Número de unidades del envase que caben en el padre (p. ej., cajas por palé). Solo para `packing`.
- **`pnt_product_dye`**: Colorante asociado (visible en tipos `final` y `semi`).
- **`pnt_product_raw`**: Materia prima asociada (visible en tipos `final` y `semi`).
- **`product_base_dye`** / **`product_base_raw`**: Colorante y materia prima base del envase (solo para `packing`).

### Peso

- **`pnt_net_weight`** (peso neto): Calculado como `pnt_parent_id.weight × pnt_parent_qty` (solo para `packing`).
- **`weight`** (peso bruto): Calculado a partir de la explosión de la LdM, sumando los pesos de todos los componentes en la cantidad correspondiente.

### Código interno y referencia automática

- **`pnt_code`**: Código de producto libre, usado como parte del código interno.
- **Botón "Auto code"** (`get_inplast_default_code`): Genera automáticamente el `default_code` del producto concatenando el código de la categoría padre, el código de categoría, el código de producto y el código de la LdM. Solo disponible para tipos `final` y `semi`.

### Nombre y variante

El nombre mostrado del producto (`display_name`) se construye incluyendo el colorante entre corchetes cuando está definido: `[REF] Nombre [Colorante]`.

En las vistas kanban y árbol se muestra también el campo `pnt_product_dye` junto al nombre.

### Propagación en cascada del nombre

Cuando se modifica el nombre de un producto de tipo `raw` o `dye`, el módulo actualiza automáticamente todos los productos de tipo `final`/`semi` que lo referencian como materia prima o colorante. Adicionalmente, propaga el cambio a los productos de tipo `packing` que tengan esos productos `final`/`semi` como padre (propagación a 2 niveles).

### Copiar variantes

Al duplicar un producto, se eliminan las traducciones del nombre para evitar heredar nombres localizados de la variante original.

---

## Categorías de Producto (`product.category`)

Los campos añadidos a la categoría son:

- **`pnt_code`** (obligatorio): Código corto de la categoría, usado en la generación automática del código interno del producto.
- **`type`** (obligatorio): Tipo de categoría, utilizado para clasificar y filtrar categorías en el contexto MRP.
- **`pnt_tolerance`**: Tolerancia porcentual de la categoría, utilizada en cálculos de producción.

---

## Certificado de Análisis / COA (`pnt.coa`)

El módulo incluye un modelo de COA (Certificate of Analysis) multilingüe asociado al producto.

### Configuración del COA

- **`pnt_product_coa`**: Campo M2O en `product.template` que enlaza el producto con su COA.
- **`pnt_product_handle_coa`**: Indica si el COA incluye gestión de manipulación.
- **`pnt_product_coa_components`**: Indica si el COA incluye la sección de componentes.

### Contenido por idioma (`pnt.coa.content`)

Al crear un COA, el sistema genera automáticamente un registro `pnt.coa.content` por cada idioma activo en la base de datos. Cada registro de contenido almacena imágenes independientes por idioma:

- **`coa_body`**: Cuerpo principal del COA.
- **`multicolor_body`**: Sección multicolor del COA.
- **`components_body`**: Sección de componentes.
- **`table_batch_certificate`**: Tabla del certificado de lote.

---

## Códigos de Cliente (`product.customer.code`)

Cada producto final puede tener una lista de códigos de cliente por partner. Los campos del modelo son:

- **`partner_id`**: Cliente al que corresponde el código.
- **`name`**: Código de producto del cliente.
- **`gtin`**: Código GTIN/EAN del producto para ese cliente.
- **`product_tmpl_id`**: Relación con el `product.template`.

Estos códigos se gestionan desde la pestaña "Wisecap" del producto, sección "Warehouse label", y son visibles solo para productos de tipo `final`.

---

## Configuración de Etiquetas

Desde la pestaña "Wisecap" del producto, sección "Warehouse label":

- **`pnt_label_type`**: Tipo de etiqueta de almacén a imprimir.
- **`number_of_labels`**: Número de etiquetas por unidad logística.
- **`pnt_customer_code_ids`**: Lista de códigos de cliente (ver apartado anterior).

Sección "Production labels":

- **`pnt_production_label_note`**: Nota que se imprime en las etiquetas de producción.

### Doble SSCC

- **`pnt_product_two_sscc`**: Indica si el producto requiere dos códigos SSCC en el etiquetado (solo para `packing`).

---

## Relaciones del Producto (pestaña "Relations")

- **`pnt_pricelist_item_ids`**: Líneas de tarifa asociadas al producto (solo lectura).
- **`pnt_packing_ids`**: Productos de tipo `packing` que referencian este producto como padre (solo lectura).
- **`pnt_bom_line_ids`**: Líneas de LdM en las que aparece este producto como componente (solo lectura).

---

## Tipos de Paquete Predefinidos (`stock.package.type`)

El módulo instala dos tipos de paquete de almacén:

| Nombre | Código | Peso máx. | Dimensiones (mm) |
|--------|--------|-----------|------------------|
| Pallet | PAL | 4.000 kg | 800 × 1.200 × 130 (alto) |
| Box | BOX | 30 kg | 362 × 374 × 562 (alto) |

---

## Configuración de Empresa (`res.company`)

Los campos añadidos a la empresa son:

- **`pnt_box_bag_id`**: Producto de tipo `packaging` utilizado como bolsa/caja de referencia de la empresa.
- **`pallet_packaging_ids`**: Lista M2M de tipos de paquete (`stock.package.type`) que se consideran palés. Se configura desde la vista de empresa con widget `many2many_tags`.

---

## Botón Pallet2Pack (`stock.picking`)

El botón **Pallet2Pack** aparece en el formulario del albarán cuando este está en estado confirmado o en proceso (no en borrador, hecho o cancelado). Está disponible para usuarios del grupo `stock.group_stock_user`.

### Funcionamiento

Al pulsar el botón, el sistema recorre todas las líneas de movimiento del albarán (`move_line_ids`) y, para cada línea:

1. Comprueba que el movimiento tenga un `product_packaging_id` definido.
2. Comprueba que el tipo de paquete del embalaje (`packaging.package_type_id`) esté incluido en `pallet_packaging_ids` de la empresa.
3. Comprueba que la línea no tenga ya un paquete destino asignado (`result_package_id`).
4. Si se cumplen las tres condiciones, lee la cantidad de la línea (`quantity`) y crea **un paquete por unidad**: la línea original se ajusta a cantidad 1 con su paquete, y se generan tantas líneas de movimiento adicionales como unidades restantes, cada una con su propio `stock.quant.package`.

Esto permite asignar automáticamente un palé individual a cada unidad del albarán, facilitando el seguimiento de la ocupación de cada palé en las estanterías del almacén.

---

## Ubicaciones de Stock (`stock.location`)

Se añade un grupo de campos de migración en el formulario de ubicación para importar la información del sistema de gestión de almacén anterior:

| Campo | Descripción |
|-------|-------------|
| `pnt_calle` | Calle de la ubicación |
| `pnt_modulo` | Módulo de la ubicación |
| `pnt_altura` | Altura de la estantería |
| `pnt_posicion` | Posición en el módulo |
| `pnt_tipopaquete` | Tipo de paquete admitido |
| `pnt_modocolocacion` | Modo de colocación |
| `pnt_huecostotales` | Total de huecos disponibles |
| `pnt_ubicaciondisponible` | Indica si la ubicación está disponible |
| `pnt_zona` | Zona del almacén |
| `pnt_udlog` | Unidad logística de referencia |

---

## Dependencias

- `product`: Modelo base de producto.
- `stock`: Albaranes, ubicaciones y paquetes.
- `account`: Categorías contables de producto.
- `mrp`: Listas de materiales y tipos de producto.
- `report_qweb_pdf_watermark`: Soporte de marca de agua en informes PDF.
- `mrp_lot_name`: Nomenclatura de lotes en producción.
- `custom_inplast`: Módulo base de personalización Inplast.
- `l10n_es_ipnr_account`: Localización española IPNR.
