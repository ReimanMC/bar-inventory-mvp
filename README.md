# Inventario La Ramona — V0.4.0

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
