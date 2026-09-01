# Inventario La Ramona — V0.4.5

## Objetivo de esta versión

V0.4.5 corrige la lógica de comparación del inventario y elimina el concepto ambiguo de **“Esperado”** en las vistas gerenciales.

La comparación operativa ahora sigue esta lógica:

**Consumo físico = Apertura + Entradas al Bar − Cierre**

**Venta por conteo = Consumo físico − Ajustes autorizados**

Los ajustes autorizados incluyen:

- Pruebas.
- Desperdicios.
- Cortesías.

Luego:

**Diferencia = Venta por conteo − Venta explicada por POS**

La alerta se genera únicamente a partir de esta última diferencia.

Ejemplo cerveza:

- Apertura Corona: 150.
- Cierre Corona: 120.
- Ajustes: 0.
- Venta por conteo: 30.
- POS: 30.
- Diferencia: 0.
- Estado: OK.

Si el POS registra 27, la diferencia es +3 y el producto pasa a revisión/alerta según la tolerancia configurada.

## POS pendiente no genera falsas alertas

Para evitar interpretar como cero un POS que todavía no se ha ingresado, la aplicación incorpora confirmación de las cuatro secciones POS:

- Cócteles.
- Shots.
- Cervezas.
- Botellas de licor.

Cada sección puede guardarse con ventas o confirmarse explícitamente en **0 ventas**.

Mientras el POS necesario no esté confirmado, el producto muestra:

**Pendiente POS**

En ese estado no se calcula diferencia ni se genera alerta.

Para cerveza basta con tener confirmado el POS de cervezas. Para licor, la comparación queda disponible cuando están confirmados Cócteles + Shots + Botellas de licor, porque las tres fuentes pueden consumir licor.

## Licores: oz + botellas equivalentes

El control interno de licor continúa realizándose en **onzas**, porque las recetas, shots y consumo teórico se manejan en oz.

Sin embargo, las vistas por producto muestran simultáneamente:

- Oz.
- Botellas equivalentes.

Ejemplo:

`19.00 oz · 0.75 bot`

Esto se aplica en el Dashboard y en el detalle del Reporte Ejecutivo para:

- Consumo físico.
- Ajustes.
- Venta por conteo.
- Venta explicada por POS/recetas.
- Diferencia.

Si la presentación en ml todavía no está configurada, la aplicación conserva las oz disponibles pero no inventa una equivalencia en botellas.

## Compras, proveedores y ventas de botellas

Las operaciones comerciales de producto completo siguen expresándose en botellas:

- Recepción de proveedor: botellas completas + fracción cuando corresponda al conteo físico.
- Traslado Bodega → Bar: botellas + fracción.
- Venta directa de botella de licor en POS: número de botellas.
- Recomendación de abastecimiento: botellas completas redondeadas hacia arriba.

En Abastecimiento, el stock y consumo de licor se presentan en **oz + botellas equivalentes**, pero la acción sugerida de compra se mantiene en **botellas completas**.

## Dashboard V0.4.5

La tabla principal cambia a:

- Producto.
- Tipo.
- Apertura.
- Cierre.
- Entradas.
- Consumo físico.
- Ajustes.
- Venta por conteo.
- Ventas POS / recetas.
- Diferencia.
- Alerta.
- Empleado.
- Hora.

Ya no existe la columna **Esperado**.

Los estados relevantes son:

- OK.
- Revisar.
- Alerta.
- Pendiente apertura.
- Pendiente cierre.
- Pendiente POS.
- Falta ml.

Las gráficas del Dashboard también cambian de **consumo real vs esperado** a **venta por conteo vs POS**.

## Reporte Ejecutivo

El reporte PDF utiliza la misma lógica del Dashboard.

Los productos con atención muestran:

- Consumo físico.
- Ajustes.
- Venta por conteo.
- POS/recetas.
- Diferencia.
- Estado.

Para licores, cada valor por producto se presenta en oz + botellas equivalentes.

Si falta confirmar el POS, el reporte informa que la comparación está pendiente y no genera una alerta falsa.

También se corrigió la proporción del logo de La Ramona en el PDF: el logo conserva su relación de aspecto original y ya no se fuerza horizontal o verticalmente.

## Exactitud

La exactitud deja de medir consumo físico contra un “esperado”. Ahora se calcula sobre la comparación relevante:

**Venta por conteo vs Venta POS**

Por tanto, desperdicios, pruebas y cortesías correctamente registrados no reducen artificialmente la exactitud.

## Reinicio de operación

El reinicio total de datos operativos continúa restringido a ADMIN/Owner y ahora también elimina las confirmaciones POS (`pos_batches`) además de:

- Inventarios.
- Conteos.
- POS.
- Movimientos operativos.

No elimina productos, recetas, usuarios, roles, configuración ni estructura de la aplicación.

## Migración

No se requiere modificar manualmente la base de datos.

V0.4.5 crea automáticamente la tabla `pos_batches` si no existe. Los registros POS anteriores continúan siendo reconocidos cuando contienen ventas; para categorías sin ventas históricas puede ser necesario usar la nueva opción **Confirmar 0 ventas** antes de realizar una comparación definitiva.

## Archivos a actualizar

Para pasar de V0.4.4 a V0.4.5:

- Reemplazar `app.py`.
- Actualizar `README.md` de forma opcional para mantener la documentación sincronizada.

No cambian:

- `requirements.txt`.
- Assets.
- Streamlit Secrets.
- Configuración OAuth.
