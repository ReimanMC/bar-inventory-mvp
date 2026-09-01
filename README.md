# Inventario La Ramona — V0.4.6

## Corrección de reconciliación de inventario

V0.4.6 corrige la interpretación de salida física, venta por conteo, POS y alertas en toda la aplicación.

### Fórmula operativa

- **Salida física** = Apertura + Entradas al bar − Cierre.
- La salida física nunca se presenta como un número negativo.
- Si el cierre supera Apertura + Entradas, la aplicación muestra **0 como salida física** y crea una incidencia de **stock aumentado sin entrada registrada**, para revisar conteo o movimientos.
- **Ajustes autorizados** incluyen Pruebas, Desperdicios, Cortesías y Roturas / botellas quebradas.
- **Venta por conteo** = max(Salida física − Ajustes autorizados, 0).
- **Diferencia** = Venta por conteo − Ventas POS / recetas.

### Interpretación de la diferencia

- **0**: el conteo y el POS coinciden dentro de la tolerancia.
- **Positiva**: el inventario físico indica más ventas/salidas que las registradas en POS; puede existir venta no registrada u otra salida no documentada.
- **Negativa**: el POS registra más ventas que las explicadas por el conteo físico; requiere revisar conteo, POS o movimientos.
- Se generan alertas en **ambos sentidos** cuando la diferencia absoluta supera la tolerancia configurada.
- Si el POS todavía no fue confirmado, la comparación permanece como **Pendiente POS**, salvo que exista una incidencia física independiente (por ejemplo, stock aumentado sin una entrada registrada).

### Unidades de licor

Los licores continúan analizándose en **onzas**, pero se muestran también como **botellas equivalentes** cuando la presentación en ml está configurada. Compras, recepción de proveedores y venta de botellas continúan operándose en botellas.

### Guía durante el conteo

- En **Apertura**, cada producto muestra de forma destacada la **BASE PARA APERTURA**, tomada del último cierre anterior disponible.
- En **Cierre**, cada producto muestra la **BASE PARA CIERRE**, tomada de la apertura del mismo día.
- Durante el cierre se muestra una estimación de Salida física, Ajustes registrados y Venta por conteo antes de guardar.

### Dashboard y reporte ejecutivo

El Dashboard y el PDF utilizan la misma lógica de reconciliación. Se reemplaza el concepto ambiguo de “Esperado” por comparación directa entre **Venta por conteo** y **Ventas POS / recetas**, e incluyen una columna de **Incidencia física** para identificar aumentos de stock no explicados o ajustes inconsistentes.

## Compatibilidad

No requiere cambios en `requirements.txt`, OAuth, Secrets ni reinicio de base de datos. Los registros existentes se recalculan con la nueva lógica al visualizar Dashboard y reportes.
