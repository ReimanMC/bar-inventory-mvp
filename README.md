# Inventario La Ramona — V0.3.8

Actualización enfocada únicamente en permisos de Administración y gestión de recetas. El resto de la V0.3.7 se mantiene sin cambios.

## 1. Administración para MANAGER y MANAGER GENERAL

Los roles siguientes ahora pueden ver **Administración**:

- `MANAGER`
- `MANAGER GENERAL` (`GENERAL_MANAGER` internamente)
- `ADMIN`

`STAFF` continúa sin acceso a Administración.

El **reinicio total de la operación** continúa protegido y visible únicamente para `ADMIN`. Un MANAGER o MANAGER GENERAL puede trabajar con productos, recetas, usuarios, importaciones y configuración operativa, pero no puede ejecutar el reinicio.

## 2. Gestión de recetas de cócteles

En **Administración → Cócteles / Recetas** se añadieron tres áreas claras:

### Crear / editar receta
- Crear un cóctel nuevo.
- Seleccionar un cóctel existente.
- Definir cuántos licores contiene.
- Seleccionar cada licor del catálogo.
- Registrar la cantidad en **onzas (oz) de licor por cóctel**.
- Guardar la receta completa o modificar una receta existente.

La receta guardada se utiliza automáticamente para calcular el consumo teórico cuando se registran ventas de ese cóctel en **POS / Ventas**.

### Importar recetas Excel
Se puede cargar directamente un archivo `.xlsx` con recetas.

La app:
- muestra una vista previa;
- permite seleccionar la hoja;
- permite seleccionar las columnas correspondientes a **Cóctel**, **Licor** y **Oz**;
- crea los cócteles que todavía no existan;
- actualiza o agrega los ingredientes de las recetas;
- informa las filas que no pudo asociar a un licor del catálogo, sin inventar equivalencias.

Incluye equivalencias operativas conocidas del catálogo actual, por ejemplo:
- Triple Sec → Triple Sec McGuinness
- Mezcal → Mezcal Ilegal
- Ron Negro → Captain Morgan Dark
- Ron Blanco → Captain Morgan White
- Vodake True / Vodka True → Vodka True

### Recetas guardadas
Muestra:
- cóctel;
- licor;
- oz de licor por cóctel;
- total de oz de licor de cada cóctel.

## 3. Sin cambios al resto de la operación

Se conserva el comportamiento de V0.3.7 para:
- inventario diario/semanal;
- licores principales configurables;
- cervezas diarias;
- POS de cócteles, shots, cervezas y botellas;
- Dashboard;
- abastecimiento;
- movimientos;
- usuarios y roles;
- autenticación;
- reinicio de datos únicamente por ADMIN.

## Archivos a actualizar

Para pasar de V0.3.7 a V0.3.8 basta con reemplazar `app.py`.

`README.md` es solo documentación. No cambian `requirements.txt`, assets ni secrets.
