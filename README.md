# Inventario La Ramona — V0.5.0

## Objetivo de esta versión

V0.5.0 refuerza el flujo operativo de **Apertura → Cierre** para evitar registros fuera de secuencia, doble/triple envío accidental y pérdida de trazabilidad. También añade confirmaciones claras y personalizadas para que cada usuario sepa exactamente qué acción quedó guardada, con su nombre, fecha y hora real.

La actualización conserva la arquitectura append-only: los conteos parciales, usuarios, timestamps y sesiones históricas permanecen almacenados sin sobrescribirse.

## 1. Flujo de inventario controlado

La aplicación determina automáticamente cuál es la única acción válida:

1. **Sin apertura:** solo se habilita **Apertura**.
2. **Apertura parcial:** Apertura continúa habilitada hasta completar los productos requeridos.
3. **Apertura completa:** solo se habilita **Cierre**.
4. **Cierre parcial:** Cierre continúa habilitado hasta completar los productos requeridos.
5. **Cierre completo:** el turno queda cerrado y la siguiente acción válida será una nueva Apertura.

La validación se realiza en la navegación y nuevamente dentro de una transacción de base de datos al guardar. Esto reduce errores cuando existen varios usuarios, pestañas abiertas o solicitudes casi simultáneas.

## 2. Cierres después de medianoche

La fecha del turno se maneja como **fecha operativa**, separada de la fecha/hora real del registro.

Ejemplo:

- Apertura: 03/09/2026 a las 4:00 PM.
- Cierre físico: 04/09/2026 a las 12:20 AM.

El cierre se conserva como:

- **Fecha operativa:** 03/09/2026.
- **Timestamp real:** 04/09/2026 12:20 AM.

Así el cambio de día no crea una nueva apertura ni rompe la comparación entre Apertura y Cierre.

## 3. Capturas parciales

Se mantiene la posibilidad de registrar:

- Todo el inventario;
- Solo cervezas;
- Solo licores.

Cada captura conserva usuario, fecha/hora real, fecha operativa, ciclo e ID de sesión. Cervezas y licores pueden registrarse a horas diferentes sin perder información.

## 4. Protección reforzada contra duplicados

V0.5.0 añade una segunda capa de protección contra doble toque, reintentos del navegador y reruns de Streamlit.

Antes de insertar una sesión, la aplicación comprueba si el mismo usuario ya guardó una captura idéntica del mismo tipo, fecha y ciclo dentro de una ventana corta. Si detecta el reintento:

- no crea otra sesión;
- no duplica los conteos;
- no duplica movimientos pendientes;
- muestra al usuario que la captura ya había sido recibida.

Además, el guardado de la sesión, todos sus conteos y los movimientos pendientes incluidos en el Cierre se realiza dentro de **una transacción SQLite atómica**. O se guarda todo correctamente o se revierte todo el intento.

## 5. Confirmaciones personalizadas para cada usuario

Después de una acción exitosa, la aplicación muestra un mensaje con:

- nombre del usuario;
- acción realizada;
- fecha y hora real en Ontario;
- fecha operativa cuando corresponde;
- estado de la captura (parcial/completa);
- cantidad de productos o registros procesados cuando aplica.

Ejemplo:

> ✅ Marlon · Su cierre fue guardado correctamente.  
> Registrado: **04/09/2026 · 12:20:18 AM**  
> Fecha operativa: **03/09/2026**  
> Cierre diario **completo** · 15/15 productos.

Las confirmaciones también se aplican a:

- recepción de productos;
- traslados Bodega → Bar;
- ventas POS de cócteles;
- ventas POS de shots;
- ventas POS de cervezas;
- ventas POS de botellas de licor;
- confirmaciones POS en cero.

## 6. Corrección controlada de capturas

Se mantiene en **Administración → Configuración / Respaldo** la herramienta exclusiva para **Developer/Owner** llamada **Corrección controlada de una captura**.

Permite corregir una sesión que realmente exista en SQLite y haya sido guardada con tipo o fecha operativa incorrectos.

La corrección:

- no elimina conteos;
- no modifica el usuario original;
- no modifica la hora real `created_at`;
- conserva el ID de sesión;
- registra una nota de auditoría;
- al convertir en Cierre exige una Apertura anterior válida del mismo ciclo y fecha operativa.

Si una captura no existe físicamente en SQLite, la herramienta no inventa ni reconstruye valores.

## 7. Trazabilidad y auditoría

Se mantiene la distinción entre:

- **Fecha operativa:** día al que pertenece el turno.
- **Fecha/hora real:** momento exacto en que el usuario guardó la captura.

El Dashboard y el detalle de auditoría continúan mostrando quién registró cada captura y a qué hora, incluso cuando diferentes categorías se ingresan en momentos distintos o después de medianoche.

## 8. Compatibilidad

No requiere cambios en:

- `requirements.txt`;
- Google OAuth;
- Streamlit Secrets;
- productos;
- recetas;
- POS existente;
- datos históricos de inventario.

No es necesario reiniciar la base SQLite.
