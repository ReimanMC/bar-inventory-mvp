# Inventario La Ramona — V0.3.1

MVP de inventario de bar en Streamlit con autenticación Google/OIDC, acceso por correo autorizado, roles, apertura/cierre, proveedores, Bodega → Bar, ajustes operativos, POS/recetas, dashboard gerencial, abastecimiento y reportes.

## Seguridad
- Login con Google.
- Solo correos autorizados y activos pueden acceder.
- Roles: STAFF, MANAGER y ADMIN.
- La cuenta `bootstrap_admin_email` en Streamlit Secrets funciona como Developer/Owner principal.
- Solo el Developer/Owner puede otorgar rol ADMIN.
- Usuarios pueden bloquearse/reactivarse sin eliminar su historial.

## V0.3.1
- Dashboard gerencial con filtros Hoy / 7 / 14 / 28 días / personalizado.
- KPIs: consumo, exactitud, alertas, mayor diferencia, costo estimado de diferencias y cobertura crítica.
- Alertas prioritarias, Top consumo, Top diferencias y tendencias real vs esperado.
- Abastecimiento muestra oz y botellas equivalentes dentro de la misma columna/celda.
- Compras recomendadas siempre en botellas/unidades enteras.
- Licores sin presentación en ml quedan marcados y no generan una recomendación engañosa.
- Consumos negativos no alimentan la estimación de compra.
- Costo por botella/unidad opcional para calcular el impacto económico de diferencias.
- Incluye `httpx` requerido por Authlib/Google OAuth.

## Streamlit Secrets
```toml
[auth]
redirect_uri = "https://TU-APP.streamlit.app/oauth2callback"
cookie_secret = "TU_COOKIE_SECRET"
client_id = "TU_CLIENT_ID"
client_secret = "TU_CLIENT_SECRET"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

[app]
bootstrap_admin_email = "TU_EMAIL"
organization_id = "LA_RAMONA"
organization_name = "La Ramona"
```

Nunca subas `client_secret`, `cookie_secret` ni `secrets.toml` a GitHub.
