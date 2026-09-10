# Inventario La Ramona — V0.5.8

## Objetivo

V0.5.8 prioriza la **captura diaria confiable y el respaldo durable**. Corrige el falso conflicto que podía aparecer durante la migración legacy cuando `latest`, `daily`, `weekly` y los slots contenían varias copias equivalentes de la misma base. Esas copias ahora se agrupan por digest y se tratan como una sola versión lógica.

También cambia el comportamiento ante fallos transitorios de Supabase: el Dashboard y los formularios siguen disponibles para consulta/diligenciamiento, pero **cada escritura operativa se revalida contra Supabase inmediatamente antes de guardar**. Una captura no se acepta si la instancia no puede demostrar que parte de la revisión durable vigente.

Para reducir condiciones de carrera, las escrituras críticas se serializan dentro del proceso Streamlit y los lotes de POS, recepciones y traslados se guardan en una sola transacción SQLite antes de crear el respaldo.

La lógica funcional de inventario, Dashboard, abastecimiento, recetas, roles, reportes y conciliación física permanece igual.

## 1. Revisión inmutable como fuente durable

Cada escritura confirmada crea una nueva revisión única bajo:

```text
revisions_v2/
  g0000000001_<timestamp>_<revision>.db
  g0000000001_<timestamp>_<revision>.meta.json
  g0000000002_<timestamp>_<revision>.db
  g0000000002_<timestamp>_<revision>.meta.json
  ...
```

Los archivos de revisión no se sobrescriben. El `.db` se valida antes y después de subirlo mediante:

- `PRAGMA quick_check`;
- digest lógico SHA-256 de los datos de negocio;
- SHA-256 del archivo SQLite completo.

La metadata incluye:

- revisión;
- generación monotónica;
- revisión padre;
- fecha/hora;
- digest de datos;
- SHA-256 del archivo;
- versión de la app;
- conteos de salud de la base.

## 2. `latest`, `daily` y `weekly` dejan de ser autoritativos

La aplicación continúa actualizando por comodidad:

```text
latest/bar_inventory_v3.db
daily/bar_inventory_YYYY-MM-DD.db
weekly/bar_inventory_YYYY-Www.db
```

pero esos archivos son únicamente copias de conveniencia para revisión/descarga manual.

La recuperación automática de V0.5.8 usa siempre `revisions_v2/`. Por tanto, una copia `latest` atrasada o servida temporalmente desde caché no puede degradar la base recuperada.

## 3. Migración automática desde V0.5.6

En el primer arranque V0.5.8:

1. busca revisiones V2;
2. si todavía no existen, revisa los respaldos legacy disponibles:
   - `latest/manifest.json` y su objeto;
   - `latest/bar_inventory_v3.db`;
   - `daily/`;
   - `weekly/`;
   - `revisions/slot_a.db` y `slot_b.db`;
3. valida cada candidato;
4. elige una copia únicamente cuando existe una relación segura de superioridad/completitud;
5. crea la primera revisión inmutable V2.

Si un manifest legacy apunta a un slot faltante, V0.5.8 puede recuperar desde un `latest`/daily/weekly válido. Además, varias copias legacy idénticas ya no se interpretan como múltiples ganadores/conflicto: se agrupan por digest y se selecciona la versión lógica que domina de forma segura a las demás.

## 4. Protección contra regresión de datos

Antes de publicar una nueva revisión la aplicación compara:

- revisión remota base;
- digest lógico;
- generación;
- usuarios/productos;
- sesiones y conteos;
- movimientos;
- POS;
- recetas y auditoría de productos.

Reglas:

- local = remoto: sincronizado;
- remoto más nuevo y local sin cambios propios: se recupera remoto;
- local es descendiente legítimo de la revisión remota: se publica nueva revisión;
- local y remoto cambiaron independientemente: conflicto, no se sobrescribe ninguna rama.

Los conflictos intentan preservarse en un objeto único bajo `conflicts/`.

## 5. Resistencia a errores transitorios

Las operaciones de Storage incorporan reintentos con backoff para:

- timeouts;
- 408/425/429;
- 500/502/503/504;
- conexiones reiniciadas/rechazadas;
- cierres inesperados de conexión;
- errores temporales de red;
- objetos recién creados que todavía no son visibles inmediatamente.

La búsqueda de la revisión V2 fue optimizada: el nombre del archivo ya contiene la generación, por lo que primero se identifica el `generation` mayor desde LIST y solo se descarga la metadata de esa generación. Esto reduce drásticamente las llamadas a Storage en cada verificación.

## 6. Protección de escritura sin bloquear la operación de consulta

Un error transitorio de Supabase durante la carga de una página **ya no oculta Apertura/Cierre/POS/Movimientos**. El usuario puede consultar y diligenciar normalmente.

Al pulsar Guardar, `_write_sync_guard()` realiza una comprobación remota fresca y obligatoria:

- local = remoto → permite guardar;
- local es descendiente legítimo con cambios aún no respaldados → respalda primero y luego permite continuar;
- remoto es más reciente → rechaza la escritura y solicita actualizar antes de guardar;
- ramas divergentes → bloquea la escritura y preserva los datos;
- Supabase no responde tras los reintentos → no acepta una nueva escritura.

Así, una indisponibilidad momentánea no deja a todos los usuarios sin poder ver la aplicación, pero tampoco permite que una captura nueva se confirme sobre una base no validada.

Las operaciones críticas usan un lock de proceso para serializar **validación → escritura → backup**, reduciendo carreras entre sesiones simultáneas de Streamlit.

## 7. SQLite local

Se conserva:

- `PRAGMA foreign_keys=ON`;
- `PRAGMA busy_timeout=30000`;
- `PRAGMA journal_mode=WAL`;
- `PRAGMA synchronous=FULL`;
- una conexión por ejecución de Streamlit;
- snapshot consistente mediante SQLite Backup API;
- eliminación de sidecars WAL/SHM al reemplazar una base durante recuperación.

## 8. Lógica operativa preservada

V0.5.8 conserva las funciones de negocio ya estabilizadas:

- Apertura → Cierre → nueva Apertura;
- cierre después de medianoche con fecha operativa correcta;
- capturas parciales y trazabilidad por usuario/hora;
- inventario diario: cervezas + licores principales;
- inventario semanal: cervezas + todos los licores activos;
- licores en botellas equivalentes y oz cuando existe ml;
- salida física y venta por conteo no negativas;
- ajustes por pruebas, desperdicios, cortesías y roturas;
- POS manual pendiente hasta su carga/confirmación;
- diferencia = venta por conteo − POS solo con POS confirmado;
- Dashboard y filtros históricos;
- abastecimiento;
- carga histórica de Apertura/Cierre Developer/Owner;
- gestión segura de productos duplicados;
- roles/permisos y Reporte Ejecutivo;
- `America/Toronto` para presentación de fechas/horas.

## 9. Validación V0.5.8

Se verificó:

- `py_compile` de `app.py`;
- selección legacy con varias copias equivalentes del mismo digest + una copia anterior: se elige la versión nueva sin falso conflicto;
- descubrimiento V2 descargando únicamente la metadata de la generación más alta;
- guard de escritura presente antes de Apertura/Cierre histórico/live, POS y movimientos;
- serialización de escrituras críticas mediante `RLock`;
- recepción de proveedor y traslado guardados en una sola transacción SQLite;
- detalle POS + confirmación de lote guardados en una sola transacción SQLite;
- segunda tentativa de backup durable después de una escritura confirmada;
- errores transitorios de lectura no ocultan los formularios, mientras el guard de escritura mantiene la protección;
- conservación de la reconciliación Apertura + Entradas − Cierre − Ajustes y POS pendiente hasta confirmación.

## 10. Actualización

Para pasar de V0.5.7 a V0.5.8:

- **antes del deploy**, descarga manualmente la SQLite actual si existe una captura reciente que todavía no esté confirmada en Supabase;
- reemplaza `app.py`;
- actualiza `README.md`;
- opcional: sube `docs/VALIDATION_V0.5.8.txt`;
- no cambia `requirements.txt`, Streamlit Secrets ni el bucket de Supabase.

No subas `.db`, Secrets, `__pycache__` ni `.pyc` a GitHub.

### Después del deploy

1. entra como Developer/Owner;
2. confirma que la versión sea V0.5.8;
3. ve a **Administración → Configuración → Estado de sincronización**;
4. confirma que local y remoto coinciden o que la base local más reciente se publique correctamente;
5. realiza una sola Apertura/Cierre controlada;
6. verifica que el mensaje confirme **Backup durable ✅**;
7. revisa desde otro usuario que el Dashboard muestre la misma actividad;
8. solo después reanuda la operación normal.
