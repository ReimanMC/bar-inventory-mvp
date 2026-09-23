Inventario La Ramona — V0.6.0
Objetivo
V0.6.0 cambia el modelo operativo diario de Apertura → Cierre a un modelo de solo Cierres consecutivos.
Los datos históricos existentes, incluidas Aperturas antiguas, no se eliminan ni se reescriben. Permanecen disponibles para auditoría. Desde esta versión, las nuevas capturas diarias se registran únicamente como Cierres.
La arquitectura de persistencia V0.5.8/V0.5.9 se mantiene: SQLite transaccional + revisiones inmutables verificadas en Supabase Storage.
1. Flujo diario
La nueva operación diaria es:
```text
Cierre anterior → Cierre actual → siguiente Cierre
```
No existe requisito de Apertura.
El Cierre puede realizarse:
a cualquier hora;
antes o después de medianoche;
el mismo día calendario o un día posterior;
por partes: solo cervezas, solo licores o todo el inventario;
por usuarios distintos mientras se completa el mismo Cierre.
La fecha operativa del cierre se selecciona independientemente de la hora real de captura. La hora real queda guardada en `created_at` para auditoría.
2. Productos del cierre diario
El Cierre diario incluye:
todas las cervezas activas;
los licores marcados como principales/diarios.
El inventario semanal permanece como proceso independiente y continúa contando todos los productos físicos activos.
3. Comparación cierre contra cierre
Para cada producto:
```text
Salida física = max(Cierre anterior + Entradas - Cierre actual, 0)
Venta por conteo = max(Salida física - Ajustes autorizados, 0)
Diferencia = Venta por conteo - POS
```
Ajustes autorizados:
Pruebas;
Desperdicios;
Cortesías;
Roturas / botellas quebradas.
Si el Cierre actual es mayor que el Cierre anterior + Entradas, el sistema no muestra consumo negativo: registra un posible aumento de stock sin entrada explicada.
4. POS pendiente
Si todavía no se ha cargado o confirmado el POS del periodo:
```text
POS = Pendiente
Diferencia = —
Estado = Pendiente POS
```
Nunca se interpreta un POS pendiente como cero.
Cuando POS se confirma en cero, entonces sí se calcula la diferencia normalmente.
5. Periodo entre cierres
Para un Cierre nuevo, el sistema congela una referencia al Cierre físico anterior. Esa referencia queda almacenada dentro de la metadata de la captura y no cambia aunque posteriormente se agreguen registros históricos.
Si el Cierre anterior corresponde a una fecha operativa anterior, los movimientos y POS se agregan sobre el periodo comprendido hasta el Cierre actual.
El primer Cierre disponible para un producto sin referencia anterior se conserva como Cierre base y no genera una diferencia falsa.
6. Capturas parciales
El primer guardado de un Cierre diario congela:
lista de productos requeridos;
fecha operativa;
identificador del ciclo de cierre;
frontera del Cierre anterior usado como referencia.
Si se guardan primero cervezas y después licores, ambas capturas pertenecen al mismo Cierre.
Cuando todos los productos requeridos han sido capturados, el Cierre queda completo y el siguiente Cierre puede iniciarse inmediatamente.
7. Datos históricos
Las Aperturas históricas existentes se conservan sin cambios, pero ya no son necesarias para los nuevos cálculos.
En Administración, la carga histórica operativa se simplifica a Cierre diario histórico, porque el modelo V0.6.0 utiliza Cierre contra Cierre.
La herramienta de corrección de sesiones conserva compatibilidad con registros antiguos.
8. Inventario semanal
El inventario semanal continúa separado del Cierre diario:
cuenta todos los productos físicos activos;
puede hacerse cualquier día;
puede guardarse por partes;
puede continuar otro usuario;
no crea ventas contra POS;
un semanal incompleto no reemplaza el stock oficial;
un semanal finalizado puede alimentar abastecimiento.
9. Abastecimiento
Para stock físico diario, la aplicación utiliza solamente Cierres diarios nuevos o históricos y los compara con inventarios semanales finalizados según la captura física más reciente.
Las Aperturas antiguas ya no desplazan un Cierre como referencia de stock.
10. Persistencia y backup
Se mantiene la arquitectura segura ya estabilizada:
```text
Escritura del usuario
    ↓
validación fresca de sincronización
    ↓
transacción SQLite
    ↓
revisión inmutable única en Supabase revisions_v2/
    ↓
verificación de integridad / SHA-256
    ↓
latest + daily + weekly como copias de conveniencia
```
No se añadieron nuevas tablas para el modelo Cierre-contra-Cierre. La metadata del ciclo se conserva dentro de `inventory_sessions.notes`, por lo que los backups y digests existentes continúan cubriendo toda la información nueva.
11. Protección de datos
Los registros históricos no se borran.
Una captura parcial no reemplaza otra captura previa; la auditoría permanece append-only.
El backup se ejecuta después de cada escritura confirmada.
Una instancia obsoleta no debe escribir sobre una revisión remota más reciente.
El inventario diario y el semanal siguen incluidos en la huella de sincronización.
12. Actualización
Para pasar de V0.5.10 a V0.6.0:
verifica que Local = Supabase y el estado esté en verde;
reemplaza `app.py`;
actualiza `README.md`;
opcional: agrega `docs/VALIDATION_V0.6.0.txt`;
no cambies `requirements.txt`;
no cambies Secrets ni el bucket de Supabase;
no subas `.db`, `__pycache__`, `.pyc` ni credenciales a GitHub.
Después del deploy, el menú diario debe mostrar únicamente Cierre e Inventario semanal como procesos físicos independientes.
