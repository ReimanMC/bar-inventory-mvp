# Inventario La Ramona — V0.4.4

## Dashboard operacional

V0.4.0 reorganiza únicamente el Dashboard para que el gerente pueda comprobar de inmediato si ya se registró inventario, incluso cuando el día todavía no tiene apertura + cierre completos.

### 1. Información en tiempo real de la operación

El Dashboard incorpora un botón **Actualizar datos** para refrescar la vista cuando otro usuario haya registrado información desde otro dispositivo.

En la parte superior se muestra:

- Estado del inventario de hoy: Sin iniciar / En progreso / Completado.
- Productos registrados frente a productos requeridos.
- Alertas críticas y productos por revisar.
- Mayor diferencia comparable.
- Cervezas vendidas en el periodo.
- Cócteles vendidos y shots vendidos en el periodo.

### 2. Estado del inventario de hoy

El Dashboard muestra separadamente:

- Cervezas registradas / pendientes.
- Licores principales registrados / pendientes en inventario diario.
- Todos los licores cuando el ciclo es semanal.
- Estado de apertura.
- Estado de cierre.
- Último usuario y hora de registro.

Un producto que todavía **no ha sido contado** aparece como **Pendiente**. No se interpreta como inventario cero y no genera una diferencia falsa.

### 3. Conteo, esperado, diferencia y alertas

En **Detalle de inventario actual** se muestra por producto:

- Producto.
- Tipo.
- Conteo actual.
- Conteo esperado cuando existe una base comparable.
- Diferencia.
- Alerta.
- Estado de registro.
- Empleado.
- Hora.

Para licores, cuando la presentación está configurada, el conteo se presenta en **botellas equivalentes + oz**.

Lógica de comparación:

- Apertura: se compara con el cierre anterior cuando existe una referencia comparable.
- Cierre: se compara con el stock esperado calculado como apertura + entradas al bar − consumo teórico POS/recetas − ajustes autorizados.
- Sin referencia: se guarda como línea base y no se crea una alerta falsa.

Estados:

- 🟢 OK / Registrado.
- 🟡 Revisar.
- 🔴 Alerta.
- ⏳ Pendiente.

### 4. Filtros del Dashboard

#### Periodo

- Hoy.
- 7 días.
- Semana actual.
- Mes actual.
- Personalizado.

#### Ver

- General.
- Licores.
- Cervezas.
- Cócteles.
- Shots.

#### Estado

- Todos.
- Con alerta.
- Pendientes.
- OK.

### 5. Cervezas

La vista de cervezas incluye:

- Conteo físico actual.
- Conteo esperado.
- Diferencia y estado.
- Consumo físico vs consumo explicado en días completos.
- Ventas registradas en POS por cerveza.
- Tendencia de consumo real vs esperado.

### 6. Licores

La vista de licores incluye:

- Conteo en botellas equivalentes y oz.
- Conteo esperado.
- Diferencia en oz.
- Estado / alerta.
- Consumo físico vs consumo explicado por POS, shots, cócteles, botellas y ajustes.
- Tendencia de consumo real vs esperado.

### 7. Cócteles

La vista de cócteles muestra:

- Cóctel.
- Cantidad vendida.
- Oz totales de licor por receta.
- Consumo teórico de licor.
- Estado de receta.

Si existen ventas de un cóctel sin receta registrada, aparece una alerta **Sin receta** porque no es posible explicar su consumo de licor.

### 8. Shots

La vista de shots muestra:

- Licor.
- Shots vendidos.
- Oz promedio por shot.
- Consumo teórico total en oz.

### 9. Actividad reciente

Se añade una vista rápida con actividad reciente de:

- Aperturas y cierres.
- Registros POS.
- Recepciones de proveedor.
- Traslados.
- Pruebas.
- Desperdicios.
- Cortesías.

Esto permite confirmar rápidamente quién registró información y cuándo.

### 10. Diferencias solo cuando existe comparación física válida

El Dashboard V0.4.0 evita marcar como faltante el consumo POS de un día que todavía no tenga apertura + cierre completos.

Las comparaciones de **consumo físico vs consumo esperado** y sus diferencias se calculan únicamente para días con ambos conteos. Las ventas siguen visibles aunque el inventario esté todavía en progreso.

## Sin cambios al resto de la aplicación

Se conservan sin modificación funcional:

- Apertura diaria/semanal.
- Cierre diario/semanal.
- Licores principales configurables.
- POS / Ventas.
- Recetas en oz.
- Abastecimiento independiente.
- Recepción de pedidos.
- Traslados.
- Usuarios y roles.
- Administración.
- Reinicio operativo exclusivo para ADMIN.
- Autenticación Google.

## Archivos a actualizar

Para pasar de V0.3.9 a V0.4.0 basta con reemplazar `app.py`.

`README.md` actualiza la documentación. No cambian `requirements.txt`, assets ni secrets.


## V0.4.1 — Zona horaria Ontario

- Corrige las horas mostradas en Dashboard, actividad reciente, inventario y auditoría para usar `America/Toronto`.
- Los timestamps siguen almacenándose internamente en UTC para mantener consistencia.
- La conversión maneja automáticamente horario de verano/invierno (EDT/EST).
- Las fechas predeterminadas de Apertura, Cierre, POS, movimientos, Dashboard, reportes y backups ahora usan la fecha local de Ontario.
- No modifica inventarios, recetas, permisos, POS ni lógica de diferencias de V0.4.0.


## V0.4.2 — Reporte Ejecutivo para propietaria

La V0.4.2 reemplaza el reporte PDF consolidado básico por un **Reporte Ejecutivo de Inventario** orientado a toma de decisiones.

### Primera página: resumen gerencial

Incluye:

- Estado del periodo: completo, parcial o sin inventario físico.
- Último registro de inventario, usuario y hora local de Ontario.
- Consumo físico de licor en oz cuando existen días comparables.
- Consumo físico de cerveza en unidades.
- Cócteles vendidos.
- Shots vendidos.
- Exactitud promedio.
- Productos con diferencia.
- Alertas críticas.
- Costo estimado de diferencias cuando existen costos configurados.
- Productos contados.
- Mayor diferencia comparable.
- Productos con compra sugerida.
- Lectura gerencial automática con los puntos que requieren atención.

### Manejo de inventarios incompletos

El reporte no interpreta como cero la información que todavía no puede calcularse.

Si no existe apertura + cierre completos, las métricas físicas se muestran como **Pendiente** o **Sin datos**, mientras que las ventas POS disponibles continúan visibles. Esto evita generar falsas diferencias o una exactitud engañosa.

### Páginas de detalle

Después del resumen ejecutivo se incluyen:

- Productos con diferencias que requieren atención.
- Consumo real vs esperado por producto.
- Ajustes autorizados.
- Diferencia y exactitud por producto.
- Costo estimado de la diferencia cuando el costo está configurado.
- Ventas POS de cócteles, shots y cervezas.
- Consumo teórico de licor por cócteles y shots.
- Abastecimiento sugerido.
- Sesiones de inventario con empleado y hora local.
- Movimientos registrados en el periodo.

### Diseño del PDF

- Identidad visual de La Ramona.
- Logo en la portada.
- Resumen ejecutivo en la primera página.
- Tablas gerenciales y operativas separadas.
- Paginación y pie de página.
- Fechas y horas mostradas en `America/Toronto`.

### Sin cambios a la operación

V0.4.2 modifica únicamente la generación del reporte y su interfaz de descarga. No cambia:

- Apertura o cierre.
- Dashboard V0.4.x.
- POS / Ventas.
- Recetas.
- Inventario diario o semanal.
- Productos.
- Roles y permisos.
- Abastecimiento de la aplicación.
- Reinicio operativo.
- Autenticación Google.
- Configuración de backup.

## Archivos a actualizar para V0.4.2

Para pasar de V0.4.1 a V0.4.2 basta con reemplazar `app.py`.

`README.md` actualiza la documentación. No cambian `requirements.txt`, assets ni Streamlit Secrets.


## V0.4.3 — Descarga de reportes restringida al desarrollador

La descarga del **Reporte Ejecutivo PDF** queda protegida por la identidad de la cuenta configurada en Streamlit Secrets como `app.bootstrap_admin_email`.

- Solo ese correo exacto puede generar y descargar el PDF ejecutivo.
- `MANAGER`, `MANAGER GENERAL` y otros usuarios `ADMIN` pueden seguir entrando a la sección **Reporte PDF** y consultar el resumen del periodo, pero no ven el botón de generación/descarga.
- La protección no depende únicamente del rol `ADMIN`; se valida el correo autenticado contra el correo bootstrap del desarrollador.
- No se requieren cambios en `requirements.txt`, assets ni estructura de base de datos.

Para pasar de V0.4.2 a V0.4.3 basta con reemplazar `app.py`.

## V0.4.4 — Autorización individual para Reporte Ejecutivo

La descarga del **Reporte Ejecutivo PDF** sigue protegida, pero ahora el Developer/Owner puede autorizar usuarios específicos sin cambiar su rol.

- La cuenta configurada en `app.bootstrap_admin_email` mantiene acceso permanente.
- Se agrega el campo interno `report_access` a la tabla `users` mediante una migración automática y compatible con la base existente.
- Desde **Administración → Usuarios → Gestionar usuario**, únicamente el Developer/Owner puede activar o revocar el permiso **Permitir generar y descargar el Reporte Ejecutivo**.
- Al crear un usuario nuevo, el Developer/Owner también puede otorgar el permiso desde el mismo formulario.
- El permiso es independiente del rol, pero para abrir la sección **Reporte PDF** el usuario debe tener un rol con acceso a esa sección: `MANAGER`, `MANAGER GENERAL` o `ADMIN`.
- `MANAGER` y `MANAGER GENERAL` pueden seguir administrando usuarios, pero no pueden otorgar ni revocar este permiso especial.
- En la tabla de usuarios aparece una columna **Reporte Ejecutivo** con los estados `Developer/Owner`, `Autorizado` o `Sin acceso`.
- No se modifican inventarios, POS, Dashboard, recetas, movimientos, reportes, costos ni reinicio operativo.

### Archivos a actualizar para V0.4.4

Para pasar de V0.4.3 a V0.4.4 basta con reemplazar `app.py`. La migración de base de datos se ejecuta automáticamente al iniciar la aplicación.

`README.md` solo actualiza la documentación. No cambian `requirements.txt`, assets ni Streamlit Secrets.

