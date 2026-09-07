# Inventario La Ramona — V0.5.2

## Objetivo de esta versión

V0.5.2 prioriza tres puntos de operación: proteger la base SQLite con Supabase Storage, permitir al Developer/Owner reconstruir aperturas y cierres históricos conservados en papel, y evitar que una diferencia contra el cierre anterior bloquee una apertura válida.

## 1. Backup automático en Supabase Storage

La configuración esperada en Streamlit Secrets es:

```toml
[supabase_backup]
enabled = true
api_url = "https://<project>.supabase.co"
secret_key = "sb_secret_..."
bucket = "la-ramona-inventory-backups"
```

La Secret Key nunca debe guardarse en GitHub.

Después de cada escritura relevante confirmada, la app crea primero un snapshot consistente de SQLite mediante la API de backup de SQLite, valida el snapshot con `PRAGMA quick_check` y luego actualiza:

- `latest/bar_inventory_v3.db` — se sobrescribe en cada cambio confirmado.
- `daily/bar_inventory_YYYY-MM-DD.db` — un único archivo por día, sobrescrito durante ese día.
- `weekly/bar_inventory_YYYY-Www.db` — un único archivo por semana, sobrescrito durante la semana.

Esto evita generar un archivo nuevo por cada clic o por cada producto. El simple `last_login_at` de un usuario no dispara un backup.

En **Administración → Configuración → Respaldo automático** el Developer/Owner puede crear/verificar un backup manual. También se mantiene la descarga manual de SQLite.

### Recuperación

Una vez exista al menos un `latest` válido en Supabase, si Streamlit pierde o reinicia la base local, V0.5.2 intenta recuperar ese `latest` validado antes de utilizar los mecanismos legacy de recuperación. Además, el Developer/Owner dispone de controles para verificar y restaurar manualmente `latest` desde Supabase.

## 2. Apertura: el conteo físico ya no se bloquea por diferencias de referencia

El cierre anterior se mantiene como **guía visual**, no como una regla que impida guardar.

Ejemplo:

- Último cierre: 42 botellas.
- Nueva apertura física: 30 botellas.

La apertura de 30 se guarda. La app puede mostrar una advertencia y una observación opcional, pero no exige una explicación para aceptar el conteo.

La diferencia entre cierre anterior y nueva apertura **no se interpreta como venta del nuevo turno**. Las ventas y diferencias del día se calculan después con la lógica operativa:

`Salida física = Apertura + Entradas al bar − Cierre`

`Venta por conteo = Salida física − Pruebas − Desperdicios − Cortesías − Roturas`

`Diferencia = Venta por conteo − Ventas POS`

La diferencia puede ser positiva o negativa; ambas direcciones generan revisión cuando superan la tolerancia configurada. Si el POS aún no está confirmado, la comparación queda pendiente y no genera una falsa alerta.

## 3. Carga histórica para Developer/Owner

En **Administración → Configuración → Carga histórica de Apertura / Cierre**, solo el Developer/Owner puede transcribir registros conservados en papel.

Se puede seleccionar:

- Fecha operativa histórica.
- Apertura o Cierre.
- Ciclo Diario o Semanal.
- Todo el inventario, solo cervezas o solo licores.
- Responsable indicado en el papel (opcional).
- Fuente/referencia y observación histórica.

La fecha/hora real en la que el Developer hace la digitación se conserva para auditoría. Los datos históricos anteriores no se borran: una nueva captura queda como un registro adicional y puede convertirse en la referencia más reciente para los productos transcritos en esa fecha.

Para registrar un **Cierre histórico**, primero debe existir una **Apertura del mismo día y ciclo**, de modo que las métricas del Dashboard y abastecimiento puedan reconciliar correctamente ambos conteos.

## 4. Trazabilidad y cálculo

Se conserva la lógica ya estabilizada de la aplicación:

- Sesiones parciales por cerveza/licor sin perder capturas anteriores.
- Apertura → Cierre → nueva Apertura en el flujo operativo en vivo.
- Cierres después de medianoche vinculados a la fecha operativa de la apertura.
- Conteos de licor en botellas equivalentes y oz cuando la presentación en ml está disponible.
- POS de cervezas, cócteles, shots y botellas de licor.
- Ajustes por pruebas, desperdicios, cortesías y roturas.
- Dashboard con salida física, venta por conteo, POS, diferencia, alertas y auditoría.
- Abastecimiento basado en días comparables, stock disponible y proyección a 7 días.

## Actualización

Para V0.5.2 solo es necesario reemplazar `app.py`. No es necesario modificar `requirements.txt`, ya que la integración con Supabase Storage usa la biblioteca estándar de Python.

No subas archivos `.db` a GitHub.
