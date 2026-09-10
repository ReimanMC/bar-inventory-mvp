# Inventario La Ramona — V0.5.7

## Objetivo

V0.5.7 corrige la causa de los bloqueos intermitentes de sincronización observados en V0.5.5/V0.5.6. La aplicación deja de usar como fuente autoritativa objetos de Supabase que se sobrescriben (`latest/manifest.json` y `revisions/slot_a.db` / `slot_b.db`).

Supabase Storage recomienda usar nuevas rutas de objeto cuando la frescura inmediata importa, porque sobrescribir una ruta puede tardar en propagarse por la capa de caché/CDN. V0.5.7 usa revisiones inmutables únicas y descubre la última revisión mediante el listado de metadatos de Storage.

La lógica funcional de inventario, Dashboard, POS, abastecimiento, carga histórica, roles, recetas, reportes y conciliación física se conserva sin cambios respecto a V0.5.6.

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

La recuperación automática de V0.5.7 usa siempre `revisions_v2/`. Por tanto, una copia `latest` atrasada o servida temporalmente desde caché no puede degradar la base recuperada.

## 3. Migración automática desde V0.5.6

En el primer arranque V0.5.7:

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

Si un manifest legacy apunta a un slot faltante, V0.5.7 puede recuperar desde un `latest`/daily/weekly válido en lugar de bloquear toda la aplicación por `NoSuchKey`.

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

Las operaciones de Storage incorporan reintentos acotados con backoff para:

- timeouts;
- 408/425/429;
- 500/502/503/504;
- errores temporales de red;
- objetos recién creados que todavía no son visibles en una lectura inmediata.

Un `NoSuchKey` de una ruta legacy opcional no se interpreta automáticamente como pérdida de conectividad.

## 6. Modo protegido

Un conflicto real o una indisponibilidad persistente de Supabase continúa bloqueando nuevas escrituras para evitar que información quede únicamente en almacenamiento temporal.

En V0.5.7 el modo protegido es menos disruptivo:

- Manager / Manager General / Admin pueden consultar Dashboard y Reporte PDF en modo lectura;
- Developer/Owner puede consultar Dashboard y Administración para diagnóstico;
- Staff recibe el mensaje de protección y no puede realizar capturas hasta recuperar la sincronización.

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

V0.5.7 no modifica las funciones de negocio ya estabilizadas:

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

## 9. Validación V0.5.7

Se verificó:

- `py_compile` de `app.py`;
- que ninguna función de negocio fuera modificada respecto a V0.5.6; los cambios se limitan a persistencia/sincronización y UX de modo protegido;
- recuperación de una base 14 sesiones / 309 conteos desde una copia remota 19 / 386;
- bootstrap legacy → primera revisión V2;
- escritura local posterior y publicación generación 2;
- recuperación de un runtime obsoleto desde la generación más nueva;
- manifest legacy apuntando a slot faltante con fallback seguro a `latest` válido;
- detección de dos ramas diferentes en la misma generación sin seleccionar una arbitrariamente;
- reconocimiento de `HTTP 400 + statusCode 404 + NoSuchKey`;
- integridad de los SQLite reales usados como referencia.

## 10. Actualización

Para pasar de V0.5.6 a V0.5.7:

- reemplaza `app.py`;
- actualiza `README.md` si deseas mantener documentación;
- opcional: sube `docs/VALIDATION_V0.5.7.txt`.

No cambia `requirements.txt`, Streamlit Secrets ni el bucket de Supabase.

No subas `.db`, Secrets, `__pycache__` ni `.pyc` a GitHub.

### Antes del deploy

Si existe una captura reciente que todavía no confirmó respaldo en Supabase, descarga manualmente la SQLite actual antes de actualizar código.

### Después del deploy

1. entra como Developer/Owner;
2. ve a **Administración → Configuración → Estado de sincronización**;
3. confirma que Local y Supabase coinciden;
4. confirma que aparece una revisión V2 / generación;
5. en Supabase Storage verifica la carpeta `revisions_v2/`;
6. realiza una única escritura real controlada;
7. confirma que la generación aumenta y que el otro usuario ve el mismo Dashboard.
