# Inventario La Ramona — V0.3.7

Actualización de roles, POS e inventario diario/semanal.

## Cambios principales

### 1. Nuevo rol MANAGER GENERAL
- Nuevo rol interno: `GENERAL_MANAGER`.
- Acceso a Dashboard, operación, POS, reportes y Administración.
- Puede gestionar productos, recetas y usuarios.
- Puede cambiar usuarios entre `STAFF`, `MANAGER` y `MANAGER GENERAL`.
- El rol `ADMIN` continúa reservado para la cuenta Developer/Owner configurada.
- El reinicio total de datos operativos sigue reservado a `ADMIN`.

### 2. Cambio de rol de usuarios
En **Administración → Usuarios** ahora se puede seleccionar un usuario y cambiar su rol.

### 3. POS / Ventas ampliado
La sección POS ahora muestra pestañas independientes para:
- Cócteles
- Shots
- Cervezas
- Botellas de licor

Las ventas de shots se convierten a consumo esperado usando las oz por shot. Las cervezas se registran directamente por unidades vendidas.

### 4. Inventario diario y semanal
Antes de realizar Apertura o Cierre se pregunta el tipo de inventario:

- **Diario:** todas las cervezas + licores principales.
- **Semanal:** todas las cervezas + todos los licores activos.

Los licores principales iniciales son:
- Jose Cuervo Silver
- Jose Cuervo Gold
- Triple Sec McGuinness
- Mezcal Ilegal
- Captain Morgan Dark
- Captain Morgan White
- Vodka True

Estos nombres corresponden al catálogo actual. La lista puede modificarse en cualquier momento.

### 5. Licores principales configurables
En **Administración → Productos → Licores principales del inventario diario** se puede añadir o quitar cualquier licor del conteo diario.

Al crear un nuevo licor también existe la opción **Incluir este licor en el inventario diario**.

### 6. Compatibilidad con la base existente
La app migra automáticamente la base V0.3.x para añadir:
- rol `GENERAL_MANAGER`;
- campo `products.daily_inventory`;
- campo `inventory_sessions.inventory_cycle`.

No elimina productos, recetas, usuarios ni datos existentes durante esta migración.

## Archivos a actualizar
Para pasar de V0.3.6 a V0.3.7 solo es necesario reemplazar `app.py`. `requirements.txt`, assets y secrets no cambian.
