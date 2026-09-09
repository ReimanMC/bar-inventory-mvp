# Inventario La Ramona — V0.5.5

## Objetivo de esta versión

V0.5.5 corrige el problema de persistencia/sincronización que permitía que una copia local antigua de SQLite volviera a sobrescribir el respaldo `latest` de Supabase. La versión conserva la lógica funcional de V0.5.4 y añade una capa de control de versiones para proteger la operación diaria.

## 1. Supabase pasa a ser la referencia durable de recuperación

En cada ejecución de Streamlit, antes de abrir SQLite, la aplicación valida la base local contra el último respaldo durable de Supabase.

- Si la base local está vacía/reiniciada y Supabase tiene una copia válida, se restaura Supabase automáticamente antes de mostrar la interfaz.
- Si Supabase contiene una versión más reciente y la base local no tiene cambios propios pendientes, se actualiza la base local automáticamente.
- Si local y Supabase contienen exactamente los mismos datos, la aplicación continúa normalmente.
- Si ambos lados cambiaron de forma independiente, la aplicación declara **conflicto** y no permite que una rama sobrescriba silenciosamente a la otra.

La recuperación integrada antigua y Google Drive quedan únicamente como contingencias posteriores; nunca pueden degradar un respaldo válido de Supabase.

## 2. Manifest + dos slots seguros

V0.5.5 ya no confía únicamente en `latest/bar_inventory_v3.db`.

Supabase mantiene:

- `latest/bar_inventory_v3.db`
- `latest/manifest.json`
- `revisions/slot_a.db`
- `revisions/slot_b.db`
- `daily/bar_inventory_YYYY-MM-DD.db`
- `weekly/bar_inventory_YYYY-Www.db`

Cada escritura confirmada usa el slot inactivo, verifica SHA-256 y solo después publica el `manifest.json`. El manifest es el punto de recuperación confirmado. Esto evita que una carga parcial o un `latest` viejo se convierta en la fuente de restauración.

Los dos slots se alternan y se sobrescriben, por lo que no se crean cientos de archivos de revisión.

## 3. Protección contra una base local antigua

Antes de publicar en Supabase la aplicación compara:

- revisión remota;
- huella lógica SHA-256 de los datos;
- sesiones de inventario;
- conteos;
- movimientos;
- POS;
- productos, usuarios y recetas.

Una base local antigua no puede avanzar `latest` si partió de una revisión remota anterior.

Si ocurre una divergencia, la copia local se intenta conservar también en:

- `conflicts/latest_conflict.db`
- `conflicts/conflict_YYYY-MM-DD.db`

sin modificar el `latest` válido.

## 4. Estado de sincronización visible para Developer/Owner

Ruta: **Administración → Configuración → Estado de sincronización**.

La pantalla muestra lado a lado:

- Local: productos, sesiones, conteos, movimientos y POS.
- Supabase: productos, sesiones, conteos, movimientos y POS.
- revisión activa;
- huella de datos;
- estado del preflight de esa ejecución.

Cuando ambos contienen la misma información aparece **✅ Sincronizado**.

## 5. Modo protegido

Si se detecta un conflicto real o no es posible validar Supabase durante una ejecución:

- los usuarios operativos no pueden continuar creando nuevas capturas en esa ejecución;
- Developer/Owner puede entrar a Administración para revisar recuperación/sincronización;
- no se permite que una base dudosa sobrescriba el respaldo durable.

La prioridad es conservar datos antes que aceptar una escritura que pueda quedar únicamente en almacenamiento temporal.

## 6. SQLite más seguro en Streamlit

La conexión SQLite se abre por ejecución con:

- `PRAGMA foreign_keys=ON`
- `PRAGMA busy_timeout=30000`
- `PRAGMA journal_mode=WAL`
- `PRAGMA synchronous=FULL`

También se eliminó la conexión SQLite persistente en `st.cache_resource`, evitando que una sesión mantenga abierto un handle hacia un archivo anterior después de una restauración.

Las restauraciones eliminan sidecars WAL/SHM antiguos antes de reemplazar el archivo principal.

## 7. Backup después de escrituras confirmadas

Se conserva el flujo:

1. escritura/transacción SQLite;
2. commit;
3. snapshot consistente con SQLite Backup API;
4. validación `PRAGMA quick_check`;
5. digest lógico;
6. carga al slot seguro;
7. verificación SHA-256;
8. actualización de `latest`, `daily` y `weekly`;
9. publicación final de `manifest.json`.

Las capturas de Apertura/Cierre mantienen `BEGIN IMMEDIATE` y protección contra reintentos/doble submit.

## 8. Lógica operativa preservada

V0.5.5 conserva lo ya validado en versiones anteriores:

- flujo Apertura → Cierre → nueva Apertura;
- cierre después de medianoche asociado a la fecha operativa correcta;
- capturas parciales por cerveza/licor con trazabilidad por usuario y hora;
- inventario diario: todas las cervezas + licores principales;
- inventario semanal: todas las cervezas + todos los licores activos;
- licor en botellas equivalentes y oz cuando existe presentación en ml;
- salida física y venta por conteo nunca negativas;
- ajustes por pruebas, desperdicios, cortesías y roturas;
- POS manual pendiente hasta que se cargue/confirme;
- diferencia = venta por conteo − POS solo cuando POS está confirmado;
- Dashboard, periodos históricos, alertas y abastecimiento;
- carga histórica de Apertura/Cierre para Developer/Owner;
- gestión segura de productos duplicados;
- roles y permisos de Reporte Ejecutivo;
- zona horaria `America/Toronto`.

## 9. Validación realizada antes de entrega

Se verificó:

- sintaxis completa de `app.py` con `py_compile` y AST;
- integridad de los backups reales de referencia;
- detección de una base antigua `14 sesiones / 309 conteos` frente a una base más completa `19 sesiones / 386 conteos`;
- restauración automática de una base local antigua cuando el remoto domina;
- bloqueo de ramas divergentes;
- preservación de una copia de conflicto sin modificar el manifest válido;
- creación inicial del manifest;
- rotación segura `slot_b → slot_a`;
- recuperación desde el slot confirmado aunque `latest/bar_inventory_v3.db` sea reemplazado por una copia vieja;
- reconciliación física: apertura 42, cierre 30 = salida/venta por conteo 12; ajustes reducen venta por conteo; stock aumentado no se convierte en consumo negativo.

## 10. Actualización

Para V0.5.5 solo debes reemplazar:

- `app.py`
- `README.md` (documentación)

No cambia `requirements.txt`, los Secrets ni el bucket existente de Supabase.

**No subas archivos `.db`, `__pycache__`, `.pyc` ni Secrets a GitHub.**

### Verificación recomendada después del deploy

1. Evita que managers registren datos durante los 2–3 minutos del redeploy.
2. Entra como Developer/Owner.
3. Ve a **Administración → Configuración → Estado de sincronización**.
4. Confirma que Local y Supabase muestran los mismos totales.
5. Debe aparecer **✅ Sincronizado** y una revisión/huella.
6. Verifica `latest/manifest.json`, `revisions/slot_a.db` o `slot_b.db`, `daily` y `weekly` en Supabase.
7. Solo después reanuda Aperturas/Cierres/POS.
