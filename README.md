# Inventario La Ramona — V0.5.4

## Objetivo de esta versión

V0.5.4 conserva todos los cambios de V0.5.3 y simplifica la **Carga histórica de Apertura / Cierre** para los casos reales en los que el inventario se hizo físicamente en papel porque la aplicación presentó un inconveniente.

## 1. Transcripción histórica sin bloqueos por valores en cero

Ruta: **Administración → Configuración → Carga histórica de Apertura / Cierre**.

La transcripción histórica ya no exige confirmar individualmente que los productos con valor `0` estaban realmente en cero. Los valores digitados, incluidos los ceros, se guardan exactamente como aparecen en el registro físico en papel.

Solo se requiere una confirmación general:

> Confirmo que este conteo fue realizado físicamente y quedó registrado en papel debido a un inconveniente del sistema, y que los valores digitados corresponden al registro físico.

Esto evita que una captura legítima quede bloqueada porque uno o varios productos tengan cero o porque falte una sesión previa en la aplicación.

## 2. Cierre histórico sin Apertura previa en el sistema

Si existe un Cierre en papel pero la Apertura correspondiente nunca pudo guardarse en la aplicación, el Developer/Owner puede transcribir el Cierre igualmente.

- El Cierre se conserva como una captura histórica independiente.
- No se inventa una Apertura ni se modifica otro día.
- Las comparaciones Apertura→Cierre permanecen **pendientes** hasta que exista una Apertura compatible.
- No se generan diferencias falsas, ventas por conteo falsas ni alertas por ausencia de la Apertura.
- Si posteriormente se transcribe la Apertura faltante, el sistema puede utilizar ambas capturas dentro de la misma fecha/ciclo.

## 3. Auditoría y trazabilidad

Cada captura histórica conserva:

- fecha operativa histórica seleccionada;
- tipo de registro: Apertura o Cierre;
- ciclo Diario/Semanal;
- responsable indicado en el documento de papel cuando se conoce;
- usuario Developer/Owner que realiza la digitación;
- fecha/hora real de transcripción;
- fuente/referencia y observaciones;
- estado de vinculación con la Apertura cuando se trata de un Cierre.

Después de guardar, el backup automático de Supabase continúa actualizando `latest`, `daily` y `weekly`.

## 4. Gestión segura de productos duplicados

Se mantiene íntegramente la funcionalidad V0.5.3 en **Administración → Productos → Gestionar producto duplicado**:

- eliminación definitiva cuando no existen referencias;
- eliminación segura cuando todas las referencias históricas tienen cantidad cero y no existen recetas con el producto;
- desactivación cuando debe conservarse el historial;
- fusión protegida con el producto correcto;
- auditoría de cambios de catálogo;
- backup automático en Supabase después de cada acción.

## 5. Funciones preservadas

V0.5.4 no modifica la lógica ya estabilizada de:

- Apertura/Cierre operativo;
- reconciliación física;
- venta por conteo;
- POS pendiente hasta confirmación manual;
- pruebas, desperdicios, cortesías y roturas;
- Dashboard y alertas;
- abastecimiento;
- recetas y licores en oz + botellas equivalentes;
- usuarios, roles y permisos;
- backup/restauración Supabase;
- recuperación SQLite y auditoría histórica.


---

# Referencia de cambios V0.5.3

## Objetivo de esta versión

V0.5.3 mantiene intacta la lógica operativa de V0.5.2 y añade una herramienta segura, exclusiva para Developer/Owner, para gestionar productos creados por duplicado sin perder trazabilidad ni alterar inventarios, POS, movimientos o recetas.

## 1. Gestión segura de productos duplicados

Ruta: **Administración → Productos → Gestionar producto duplicado**.

Antes de permitir una acción, la app revisa todas las relaciones del producto en:

- `inventory_counts` — conteos históricos de Apertura/Cierre.
- `movements` — proveedor, traslados, pruebas, desperdicios, cortesías y roturas.
- `pos_sales` — ventas POS manuales.
- `recipes` — ingredientes de cócteles.

La interfaz muestra cuántas filas existen en cada módulo y cuántas contienen una cantidad distinta de cero.

### Caso A — 0 registros relacionados

Si el producto nunca fue utilizado (`0` referencias totales), se habilita **Eliminar producto definitivamente**. La eliminación es segura porque no existe información operativa que dependa de ese producto.

### Caso B — solo referencias con cantidad 0

Si el duplicado tiene filas históricas pero **todas las cantidades son 0**, no tiene movimientos/POS con valor y **no participa en recetas**, se habilita **Eliminar duplicado con referencias en cero**.

La app elimina únicamente esas referencias cero y después retira el producto. Esto evita conservar un duplicado que nunca tuvo stock/venta real, sin borrar cantidades físicas ni ventas. La acción requiere escribir la frase de confirmación `ELIMINAR DUPLICADO CERO`.

> Importante: un conteo actual de stock igual a 0 no basta para borrar un producto. La app comprueba también todo su historial.

### Caso C — el producto sí tiene información con valor

No se permite el borrado directo. El Developer/Owner puede:

- **Desactivar producto**: deja de aparecer en nuevos inventarios/operaciones, pero conserva todo el historial.
- **Fusionar con el producto correcto**: reasigna sus conteos, movimientos, POS y recetas al producto seleccionado y retira el duplicado.

La fusión automática se bloquea si:

- los productos pertenecen a categorías diferentes;
- ambos tienen presentaciones `ml` conocidas y diferentes;
- los tipos de envase son diferentes;
- existen sesiones donde ambos productos tienen conteos no cero;
- ambos aparecen con cantidades en la misma receta.

Estas restricciones evitan sumar inventarios accidentalmente o reinterpretar botellas históricas con una presentación incorrecta.

## 2. Auditoría de cambios de catálogo

V0.5.3 crea la tabla `product_admin_audit`. Toda acción de eliminación, limpieza de referencias cero, fusión, desactivación o reactivación registra:

- producto origen;
- producto destino cuando aplica;
- usuario Developer/Owner;
- fecha/hora real;
- tipo de acción;
- resumen de referencias que existían antes del cambio.

Después de cada acción confirmada se ejecuta inmediatamente el backup normal de la aplicación, por lo que `latest`, `daily` y `weekly` de Supabase quedan actualizados.

## 3. Detección de posibles duplicados

La sección muestra posibles duplicados utilizando una comparación normalizada por categoría y nombre (ignora mayúsculas, acentos y separadores). La selección para actuar se realiza por nombre, categoría y presentación; no es necesario memorizar IDs internos.

## 4. Lo que no cambia

Se conserva todo lo estabilizado en V0.5.2:

- backup automático y restauración con Supabase Storage;
- `latest`, `daily` y `weekly`;
- carga histórica de Apertura/Cierre para Developer/Owner;
- flujo Apertura → Cierre → nueva Apertura;
- cierres después de medianoche asociados a la fecha operativa correcta;
- conteos parciales y trazabilidad por usuario/hora;
- licores en botellas equivalentes y oz cuando existe presentación en ml;
- POS pendiente hasta que sea cargado o confirmado explícitamente;
- salida física, venta por conteo, diferencias y alertas del Dashboard;
- abastecimiento y reporte ejecutivo.

## Actualización

Para V0.5.3 solo es necesario reemplazar `app.py` y, opcionalmente, actualizar este `README.md`. No cambia `requirements.txt`, Secrets ni la estructura existente de Supabase.

No subas archivos `.db` a GitHub.
