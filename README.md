# Inventario La Ramona — V0.5.9

## Objetivo

V0.5.9 separa completamente el **inventario diario** del **inventario semanal** sin modificar la arquitectura de persistencia y respaldo estabilizada en V0.5.8.

La prioridad continúa siendo que cada captura confirmada quede primero en SQLite mediante una transacción segura y después se publique como una revisión inmutable validada en Supabase Storage.

## 1. Inventario diario

El flujo diario queda exclusivamente como:

```text
Apertura diaria → Cierre diario → nueva Apertura
```

Incluye:

- todas las cervezas activas;
- únicamente los licores marcados como principales/diarios;
- capturas parciales de cervezas o licores;
- trazabilidad por usuario y hora;
- comparación física posterior con POS cuando POS haya sido cargado o confirmado.

El selector Diario/Semanal fue retirado de Apertura y Cierre para evitar mezclar procesos distintos.

Los registros WEEKLY antiguos que ya existan en `inventory_sessions` se conservan para auditoría, pero ya no participan en el flujo operativo diario.

## 2. Inventario semanal independiente

Se agrega una nueva opción en el menú lateral:

```text
📋 Inventario semanal
```

Está disponible para STAFF, MANAGER, MANAGER GENERAL y ADMIN cuando la sincronización permite escrituras.

Características:

- puede iniciarse cualquier día según disponibilidad del equipo; la fecha operativa se toma automáticamente del día en que se inicia;
- cuenta **todos los productos físicos activos** de Cerveza y Licor;
- no requiere Apertura/Cierre;
- no modifica ni bloquea el turno diario;
- no genera diferencias contra POS;
- puede guardarse por partes;
- puede continuar otro usuario en otro momento;
- conserva quién ingresó cada captura y a qué hora;
- puede recontarse un producto antes de finalizar;
- solo se finaliza cuando todos los productos requeridos tienen un conteo.

Un inventario semanal en progreso no se usa todavía como stock oficial. Solo un inventario semanal **COMPLETED** puede convertirse en referencia física para abastecimiento.

## 3. Nuevas tablas de auditoría semanal

V0.5.9 añade:

```text
weekly_inventory_sessions
weekly_inventory_session_products
weekly_inventory_captures
weekly_inventory_counts
```

### `weekly_inventory_sessions`

Conserva fecha física, estado, usuario/hora de inicio y usuario/hora de finalización.

### `weekly_inventory_session_products`

Congela la lista de productos requeridos al iniciar el inventario. Si posteriormente se crea un producto nuevo, no cambia el progreso de un inventario semanal que ya estaba en curso.

### `weekly_inventory_captures`

Cada vez que un usuario pulsa **Guardar avance semanal** se conserva una captura independiente.

### `weekly_inventory_counts`

Conserva cada conteo físico por producto, usuario y hora. Los re-conteos son append-only: no borran el registro anterior; el conteo más reciente dentro de la sesión es la referencia vigente.

## 4. Concurrencia multiusuario

El inventario semanal incorpora protección adicional para varios usuarios:

- solo puede existir un inventario semanal `IN_PROGRESS` a la vez;
- iniciar dos veces no genera dos sesiones activas;
- cada guardado se serializa con el mismo lock de escrituras durables usado por la operación diaria;
- antes de escribir se revalida Supabase;
- si otro usuario actualizó un producto después de que la pantalla fue cargada, el sistema bloquea la sobrescritura y solicita actualizar la página;
- si otro usuario finaliza la sesión mientras alguien mantiene un formulario antiguo abierto, el formulario antiguo no puede guardar sobre una sesión finalizada.

## 5. Cantidades

### Cerveza

Se registra en unidades/botellas.

### Licor

Se registra como:

- botellas completas;
- 0.25;
- 0.50;
- 0.75.

Cuando existe `bottle_ml`, la aplicación conserva además la equivalencia en oz. Si falta ml, conserva la cantidad en botellas equivalentes y puede convertirla posteriormente cuando se complete la presentación.

No se exige confirmar que un valor cero sea un error: el cero puede ser un conteo físico válido.

## 6. Abastecimiento

`current_stock_basis()` ahora compara dos fuentes físicas:

1. el conteo diario más reciente;
2. el conteo semanal **finalizado** más reciente.

Se usa el que haya sido capturado más recientemente y luego se aplican los movimientos posteriores.

Esto permite que los licores secundarios, que normalmente no aparecen en el inventario diario, tengan un stock físico actualizado después del inventario semanal.

Un semanal incompleto nunca altera abastecimiento.

## 7. Backup y sincronización

Se conserva sin degradaciones la arquitectura V0.5.8:

```text
SQLite transaccional
    ↓
validación previa contra Supabase
    ↓
revisions_v2/<revisión única>.db
    ↓
validación de integridad / digest
    ↓
latest / daily / weekly (copias de conveniencia)
```

Las nuevas tablas semanales fueron añadidas al digest lógico y al estado de salud de sincronización. Por tanto, una captura semanal cambia la huella de datos y debe quedar respaldada en Supabase igual que Apertura, Cierre, POS o movimientos.

En **Administración → Configuración → Estado de sincronización** se muestran por separado:

- sesiones/conteos diarios;
- sesiones/conteos semanales;
- movimientos;
- POS.

## 8. Recuperación

Los backups antiguos V0.5.8 siguen siendo válidos. Al abrirlos en V0.5.9, las tablas semanales se crean por migración sin modificar los datos diarios históricos.

El respaldo integrado antiguo continúa siendo únicamente un último recurso cuando no existe una copia válida en Supabase.

## 9. Productos duplicados

La gestión segura de duplicados ahora considera también referencias del inventario semanal.

Un producto que ya forma parte de una fotografía semanal no se elimina/fusiona de forma destructiva. En esos casos se recomienda desactivarlo para preservar la trazabilidad histórica.

## 10. Reinicio total

La herramienta ADMIN **Dejar operación en cero** elimina también:

- sesiones semanales;
- capturas semanales;
- conteos semanales;

además de inventario diario, POS y movimientos.

Sigue conservando productos, recetas, usuarios, roles y configuración.

## 11. Validación V0.5.9

Se verificó:

- `py_compile` de `app.py`;
- migración sobre un backup real con 12 usuarios, 69 productos, 19 sesiones diarias y 386 conteos diarios;
- creación del inventario semanal sin alterar las tablas diarias;
- guardado parcial y reanudación hasta 69/69 productos;
- finalización del semanal y `PRAGMA quick_check = ok`;
- `PRAGMA foreign_key_check` sin errores;
- restricción de una sola sesión semanal activa;
- inventario semanal incompleto excluido de stock/abastecimiento;
- inventario semanal finalizado seleccionado como stock cuando es el conteo físico más reciente;
- tablas semanales incluidas en digest/sincronización con orden canónico estable;
- migración V0.5.8 → V0.5.9 publicada como descendiente legítimo antes de nuevas escrituras;
- eliminación del selector Semanal de Apertura/Cierre;
- navegación semanal disponible como proceso independiente;
- protección de concurrencia por producto antes de sobrescribir un re-conteo.

Consulta `docs/VALIDATION_V0.5.9.txt` para el detalle.

## 12. Actualización

Para pasar de V0.5.8 a V0.5.9:

1. confirma que **Administración → Configuración → Estado de sincronización** esté en verde antes del deploy;
2. reemplaza `app.py`;
3. actualiza `README.md`;
4. opcional: agrega `docs/VALIDATION_V0.5.9.txt`;
5. no cambies `requirements.txt`;
6. no cambies Streamlit Secrets;
7. no cambies el bucket de Supabase;
8. no subas `.db`, Secrets, `__pycache__` ni `.pyc` a GitHub.

Después del deploy, verifica que Local y Supabase coincidan. Luego puede iniciarse un inventario semanal desde la nueva opción independiente sin afectar la Apertura/Cierre diaria.
