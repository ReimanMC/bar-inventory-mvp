# Inventario La Ramona — V0.4.8

## Objetivo de esta versión

V0.4.8 corrige la lectura y reconciliación de inventarios cuando existen varios registros el mismo día, realizados por diferentes usuarios y a diferentes horas. La actualización es **no destructiva**: no elimina ni reemplaza aperturas, cierres, conteos, POS o movimientos históricos.

## 1. Apertura y cierre vinculados por sesión

Cada cierre nuevo guarda como metadato la apertura más reciente del mismo ciclo y, para cada producto, la reconciliación utiliza el conteo de apertura más reciente del mismo día/ciclo registrado antes de ese cierre. Esto evita mezclar por error:

- una apertura diaria con un cierre semanal;
- una apertura semanal con un cierre diario;
- registros hechos a distintas horas;
- correcciones o conteos repetidos del mismo día.

Para cierres históricos existentes, la aplicación crea únicamente el vínculo de metadatos con la apertura del mismo día y ciclo registrada antes del cierre. **Los valores originales de inventario no se modifican.**

Si existen varias capturas del mismo ciclo, cada producto conserva su usuario, hora e ID de sesión. La aplicación usa la captura más reciente aplicable a ese producto y todos los registros permanecen disponibles en el historial.


## 2. Capturas parciales sin convertir pendientes en cero

Apertura y Cierre permiten elegir **Todo el inventario**, **Solo cervezas** o **Solo licores**. Esto permite que diferentes personas completen el inventario a distintas horas sin crear falsos ceros para productos que todavía no han sido contados.

Cada captura se agrega al historial. Para reconciliar cada producto, la aplicación utiliza el conteo más reciente del **mismo día, mismo ciclo y mismo producto**. Así, una captura de cervezas a una hora y una captura de licores más tarde pueden coexistir sin sobrescribirse.

Si un producto realmente queda en cero, la aplicación solicita una confirmación explícita antes de guardar. Esto evita que un campo dejado en su valor inicial `0` sea interpretado accidentalmente como un conteo físico real.

## 3. Corrección del Dashboard histórico

El Dashboard reconcilia cada producto únicamente con registros del mismo día y del mismo ciclo de inventario. Puede combinar de forma segura capturas parciales hechas a distintas horas, pero nunca mezcla un registro diario con uno semanal.

En fechas con varias capturas, el historial permite revisar todas las sesiones y el Dashboard utiliza el registro más reciente aplicable a cada producto sin eliminar información.

La lógica continúa siendo:

- **Salida física = Apertura + Entradas al bar − Cierre**
- **Venta por conteo = max(Salida física − Ajustes autorizados, 0)**
- **Diferencia = Venta por conteo − Ventas POS / recetas**

Una diferencia positiva o negativa puede generar alerta si supera la tolerancia configurada.

## 4. Licores sin presentación en ml

Los conteos de licor ya no aparecen como `0 oz` cuando la presentación en ml todavía no ha sido configurada.

Mientras falten los ml, la aplicación conserva y muestra la cantidad física en **botellas equivalentes**, por ejemplo:

`2.25 bot · oz pendiente`

También calcula en botellas:

- Salida física;
- Entradas;
- Pruebas;
- Desperdicios;
- Cortesías;
- Roturas;
- Venta por conteo física.

La comparación contra cócteles, shots y recetas permanece como **Falta ml para POS** porque las recetas están expresadas en onzas. Cuando se registre la presentación en ml, la conversión histórica a oz se realiza con el mecanismo de backfill existente.

## 5. Abastecimiento y stock

Abastecimiento mantiene por defecto el análisis de **últimos 7 días** y la proyección para los próximos 7 días.

- Cervezas: unidades.
- Licor con ml configurado: oz + botellas equivalentes; compra sugerida en botellas completas.
- Licor con ml pendiente: el control puede continuar en botellas equivalentes y la compra se expresa en botellas completas.

El cálculo de stock actual también incorpora movimientos registrados después del último conteo, incluso cuando ocurren el mismo día.

## 6. Trazabilidad y conservación de datos

El Dashboard incorpora un detalle de auditoría que muestra:

- ID de sesión;
- fecha;
- hora local de Ontario;
- usuario;
- tipo Apertura/Cierre;
- ciclo Diario/Semanal;
- producto;
- conteo registrado en la unidad correcta.

Para licores sin ml se muestra el conteo real en botellas equivalentes en lugar de `0 oz`.

Además, **Historial íntegro de sesiones** permite verificar todos los registros realizados a diferentes horas. Una nueva sesión no borra las anteriores.

## 7. Cierre con base visible

Al realizar un cierre, cada producto busca únicamente una apertura del **mismo día y mismo ciclo**. La base visible incluye usuario, hora e ID de sesión para que el empleado pueda comprobar de dónde proviene el valor de referencia.

El cierre conserva además un vínculo de metadatos con la apertura más reciente del ciclo, mientras la reconciliación por producto mantiene la trazabilidad exacta de capturas parciales.

## 8. Reporte Ejecutivo

El PDF utiliza la misma reconciliación por sesiones. Los licores sin ml se conservan en botellas equivalentes y se presentan como pendientes de conversión, sin generar valores falsos de `0 oz` ni comparaciones POS incorrectas.

## Compatibilidad

No requiere cambios en `requirements.txt`, Google OAuth, Streamlit Secrets ni reinicio de la base de datos.

La migración V0.4.8 añade únicamente el campo de vínculo `paired_opening_session_id` e índices de lectura. Los registros históricos permanecen intactos.
