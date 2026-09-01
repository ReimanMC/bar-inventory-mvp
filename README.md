# Inventario La Ramona — V0.4.7


## Corrección de periodos históricos en Dashboard

V0.4.7 corrige el Dashboard para que **Periodo**, incluyendo **Personalizado**, controle también el bloque operacional. Cuando el rango incluye varios días, la aplicación localiza el **último día con inventario realmente registrado dentro del rango** y lo usa como fecha de referencia para Estado de inventario, Productos registrados, alertas prioritarias y Detalle de inventario. Esto evita que un rango como 31/08/2026–01/09/2026 aparezca vacío solo porque el día actual todavía no tiene apertura.

- El KPI cambia a **Último inventario** cuando se consulta un periodo histórico o de varios días.
- El Dashboard muestra la fecha exacta usada como referencia.
- El detalle físico presenta Apertura, Cierre, Entradas, Salida física, Ajustes, Venta por conteo, POS y Diferencia del último inventario dentro del periodo.
- **Venta por conteo vs POS**, ventas y tendencias continúan agregándose para todo el rango seleccionado.

## Abastecimiento cada 7 días

La pantalla **Abastecimiento** incorpora **Últimos 7 días** como opción y queda seleccionada por defecto. La recomendación continúa proyectando la necesidad para los **próximos 7 días**, con el margen de seguridad configurado. Se mantienen también 14, 21, 28, 42 y 56 días como históricos alternativos.

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
