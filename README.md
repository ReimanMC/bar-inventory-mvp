# Inventario La Ramona — V0.3

MVP móvil/web para inventario de bar con apertura/cierre, Bar/Bodega, proveedores, traslados, ajustes, POS, recetas, dashboard consolidado, alertas, abastecimiento semanal y reportes PDF.

## Seguridad V0.3

V0.3 elimina el acceso operativo mediante PIN compartido y usa inicio de sesión Google (OIDC) de Streamlit.

- Solo correos previamente autorizados y activos pueden entrar.
- Compartir el enlace de la app no concede acceso.
- ADMIN puede autorizar, bloquear, reactivar y cambiar roles STAFF / MANAGER / ADMIN.
- Cada operación conserva el usuario autenticado.
- El primer ADMIN se define mediante un secreto de Streamlit, no dentro de GitHub.

## Archivos para GitHub

Reemplaza `app.py`, `requirements.txt` y `README.md` por los de esta versión. No subas `secrets.toml`, Client Secret ni credenciales a GitHub.

## Configuración necesaria en Streamlit Community Cloud

En **App settings → Secrets**, agrega:

```toml
[auth]
redirect_uri = "https://TU-APP.streamlit.app/oauth2callback"
cookie_secret = "UNA-CADENA-ALEATORIA-LARGA-Y-SECRETA"
client_id = "TU_GOOGLE_CLIENT_ID"
client_secret = "TU_GOOGLE_CLIENT_SECRET"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

[app]
bootstrap_admin_email = "TU_CORREO_GOOGLE"
```

El mismo `redirect_uri` debe estar registrado como **Authorized redirect URI** en el cliente OAuth Web de Google Cloud.

## Primera entrada

1. Configura Google OAuth y los Secrets.
2. Abre la app y pulsa **Continuar con Google**.
3. Entra con el correo definido en `bootstrap_admin_email`.
4. Ve a **Administración → Usuarios** y autoriza los correos del personal.
5. Desde allí puedes bloquear/reactivar usuarios y asignar roles.

## Nota de persistencia

SQLite es suficiente para pruebas del MVP, pero Streamlit Community Cloud no debe considerarse almacenamiento operativo permanente. Antes de depender de la aplicación como sistema definitivo multiusuario, migra la base de datos a un servicio persistente como PostgreSQL/Supabase.
