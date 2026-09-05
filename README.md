# Inventario La Ramona — V0.5.1

## Objetivo de esta versión

V0.5.1 es una versión de recuperación segura construida sobre V0.5.0. Su objetivo es restaurar automáticamente el último respaldo SQLite validado proporcionado por el Developer/Owner cuando Streamlit inicia con una base ausente o claramente reiniciada, sin sobrescribir una base que ya contiene operación válida.

## Respaldo integrado y validado

El snapshot de recuperación integrado corresponde al archivo proporcionado por el Developer/Owner y fue validado con `PRAGMA quick_check = ok`.

Contenido del snapshot:

- 12 usuarios autorizados y activos.
- 67 productos.
- 14 sesiones de inventario.
- 309 conteos físicos.
- 1 cóctel y 2 componentes de receta.
- 0 movimientos registrados en ese respaldo.
- 0 filas POS registradas en ese respaldo.

La restauración conserva nombres, emails, roles, permisos de Reporte Ejecutivo, fechas de login e historial existente exactamente como están en el respaldo. Todos los usuarios contenidos en el snapshot tienen `active = 1`.

## Recuperación automática segura

Antes de abrir SQLite, la aplicación:

1. intenta el mecanismo de recuperación Drive ya existente, si está configurado;
2. valida la base local con `PRAGMA quick_check` y tablas requeridas;
3. si la base está ausente o presenta el patrón de reinicio observado (0 sesiones, 0 conteos y 0/1 usuarios), restaura el snapshot integrado;
4. si la base ya tiene operación válida, no realiza ninguna restauración.

Antes de una recuperación automática sobre un archivo existente, intenta conservar una copia local de contingencia con nombre `bar_inventory_v3_before_auto_recovery_*.db`.

## Recuperación manual desde la aplicación

Solo el Developer/Owner dispone ahora de una sección **Administración → Configuración → Recuperación de base de datos**.

Desde allí puede:

- ver el estado de salud y los conteos de la base actual;
- cargar un `.db`, `.sqlite` o `.sqlite3`;
- validar integridad y tablas antes de restaurar;
- visualizar usuarios activos, productos, sesiones, conteos, movimientos y POS del respaldo candidato;
- confirmar la restauración escribiendo `RESTAURAR BASE`;
- reemplazar la base sin volver a desplegar código.

Antes de una restauración manual se conserva una copia local de contingencia `bar_inventory_v3_before_manual_restore_*.db`.

## Autorización de usuarios restaurados

Los 12 usuarios incluidos en el respaldo están activos. Se conservan sus roles:

- ADMIN / Developer-Owner.
- MANAGER.
- GENERAL_MANAGER.
- STAFF.

La cuenta configurada en `bootstrap_admin_email` continúa teniendo la protección existente: al iniciar sesión se garantiza que permanezca activa como ADMIN y con acceso al Reporte Ejecutivo.

## Importante sobre el alcance del respaldo

V0.5.1 restaura únicamente lo que existe físicamente en el respaldo suministrado. No reconstruye registros que nunca llegaron a SQLite. En particular, el snapshot conserva la información existente hasta la apertura registrada del 03/09; no inventa un cierre posterior que no esté contenido en el archivo.

## Persistencia

El snapshot integrado funciona como un **piso de recuperación**, no como backup continuo. Los registros nuevos posteriores a ese snapshot siguen necesitando respaldo periódico. La opción **Descargar copia de la base SQLite** continúa disponible y más adelante debe complementarse con un almacenamiento persistente automático.

## Compatibilidad

No requiere cambios en:

- `requirements.txt`;
- Google OAuth;
- Streamlit Secrets;
- assets/logo.

Para desplegar la recuperación automática basta con reemplazar `app.py`. El paquete también incluye `bar_inventory_v3.db` y `bar_inventory_restore_2026_09_03.db` como copias verificables del respaldo fuente.
