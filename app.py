import streamlit as st
import sqlite3, hashlib, io, math, re, unicodedata, json, os
from datetime import datetime, date, timedelta
import pandas as pd
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

DB = "bar_inventory_v3.db"
ML_PER_OZ = 29.5735295625
DEFAULT_TOL_BEER = 1.0
DEFAULT_TOL_LIQUOR = 1.0

st.set_page_config(page_title="Inventario La Ramona", page_icon="❤️", layout="wide", initial_sidebar_state="expanded")

LOGO_PATH = "assets/la_ramona_logo.webp"

st.markdown("""
<style>
:root{
  --ramona-orange:#ff6a00;
  --ramona-orange-soft:rgba(255,106,0,.12);
  --ramona-red:#d9272e;
  --panel:#171c22;
  --panel-2:#1d232b;
  --line:rgba(255,255,255,.10);
  --muted:#9ea7b3;
}
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"]{
  background:#0d1117;
}
.block-container{padding-top:4.4rem;padding-bottom:3rem;max-width:1450px}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#10151b 0%,#0b1015 100%);border-right:1px solid var(--line)}
[data-testid="stSidebar"] .block-container{padding-top:1rem}
[data-testid="stSidebar"] img{max-width:185px;margin:0 auto .3rem auto;display:block}
[data-testid="stSidebar"] hr{border-color:var(--line)}
[data-testid="stSidebar"] [role="radiogroup"] label{padding:.48rem .62rem;border-radius:9px;margin:.12rem 0}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:var(--ramona-orange-soft);border:1px solid rgba(255,106,0,.20)}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p{color:#ff7a18;font-weight:700}
div[data-testid="stMetric"]{background:linear-gradient(180deg,var(--panel-2),var(--panel));border:1px solid var(--line);padding:15px 16px;border-radius:12px;box-shadow:0 5px 18px rgba(0,0,0,.14)}
div[data-testid="stMetric"] label{color:#c5ccd5!important}
div[data-testid="stMetric"] [data-testid="stMetricValue"]{font-weight:800}
.stButton>button[kind="primary"], .stDownloadButton>button{background:linear-gradient(90deg,#e74b4d,#ef6a4c);border:0;border-radius:10px;font-weight:700}
.stButton>button{border-radius:9px}
[data-testid="stExpander"], [data-testid="stDataFrame"], [data-testid="stTable"]{border-radius:11px;overflow:hidden}
[data-testid="stExpander"]{border:1px solid var(--line);background:rgba(255,255,255,.015)}
[data-baseweb="tab-list"]{gap:.25rem}
[data-baseweb="tab"]{border-radius:8px 8px 0 0}
[data-baseweb="tab"][aria-selected="true"]{color:#ff7a18}
.ramona-page-header{display:flex;align-items:flex-start;justify-content:space-between;gap:1rem;margin:.35rem 0 1.2rem 0;position:relative;z-index:1}
.ramona-page-title{font-size:2rem;font-weight:800;line-height:1.15;margin:0;color:#f7f8fa}
.ramona-page-subtitle{margin-top:.35rem;color:var(--muted);font-size:.95rem}
.ramona-badge{display:inline-block;padding:.22rem .55rem;border-radius:999px;background:var(--ramona-orange-soft);color:#ff7a18;border:1px solid rgba(255,106,0,.25);font-size:.76rem;font-weight:700}
.ramona-section{font-size:1.18rem;font-weight:750;margin:1.2rem 0 .6rem}
.ramona-note{color:var(--muted);font-size:.88rem}
.ramona-login-wrap{max-width:720px;margin:5vh auto 0 auto;text-align:center}
.ramona-login-wrap img{max-width:320px;width:72%;margin:0 auto 1rem auto}
.small-note{font-size:.86rem;opacity:.75}
@media (max-width: 700px){
  .block-container{padding-left:.7rem;padding-right:.7rem;padding-top:3.8rem}
  div[data-testid="stHorizontalBlock"]{gap:.35rem}
  .ramona-page-title{font-size:1.55rem}
}
</style>
""", unsafe_allow_html=True)

try:
    st.logo(LOGO_PATH, size="large", icon_image=LOGO_PATH)
except Exception:
    pass

def page_header(title, subtitle="", badge="V0.3.7"):
    st.markdown(f"""
    <div class="ramona-page-header">
      <div>
        <div class="ramona-page-title">{title}</div>
        <div class="ramona-page-subtitle">{subtitle}</div>
      </div>
      <div class="ramona-badge">{badge}</div>
    </div>
    """, unsafe_allow_html=True)


# ---------------------- optional Google Drive backup ----------------------
def _gdrive_cfg():
    try:
        sec=st.secrets.get("gdrive", {})
        return {"enabled": bool(sec.get("enabled", False)), "folder_id": str(sec.get("folder_id", "")).strip(), "service_account_json": str(sec.get("service_account_json", "")).strip()}
    except Exception:
        return {"enabled": False, "folder_id": "", "service_account_json": ""}

def _drive_service():
    cfg=_gdrive_cfg()
    if not (cfg["enabled"] and cfg["folder_id"] and cfg["service_account_json"]): return None
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        creds=Credentials.from_service_account_info(json.loads(cfg["service_account_json"]), scopes=["https://www.googleapis.com/auth/drive"])
        return build("drive","v3",credentials=creds,cache_discovery=False)
    except Exception:
        return None

def _find_drive_file(service,name,folder_id):
    safe=name.replace("'","\\'")
    res=service.files().list(q=f"name='{safe}' and '{folder_id}' in parents and trashed=false",spaces='drive',fields='files(id,name,modifiedTime)',pageSize=10).execute()
    files=res.get('files',[]); return files[0] if files else None

def backup_db_to_drive(force=False):
    service=_drive_service(); cfg=_gdrive_cfg()
    if not service or not os.path.exists(DB): return False,"Respaldo Drive no configurado"
    try:
        from googleapiclient.http import MediaFileUpload
        folder=cfg['folder_id']
        for name in ['bar_inventory_v3_latest.db',f"bar_inventory_v3_{date.today().isoformat()}.db"]:
            media=MediaFileUpload(DB,mimetype='application/octet-stream',resumable=False)
            found=_find_drive_file(service,name,folder)
            if found: service.files().update(fileId=found['id'],media_body=media).execute()
            else: service.files().create(body={'name':name,'parents':[folder]},media_body=media,fields='id').execute()
        st.session_state['_last_drive_backup']=datetime.now().isoformat(timespec='seconds')
        return True,"Respaldo actualizado en Google Drive"
    except Exception as e:
        st.session_state['_drive_backup_error']=str(e)
        return False,f"No se pudo respaldar en Drive: {e}"

def restore_db_from_drive_if_missing():
    if os.path.exists(DB) and os.path.getsize(DB)>0: return
    service=_drive_service(); cfg=_gdrive_cfg()
    if not service: return
    try:
        from googleapiclient.http import MediaIoBaseDownload
        found=_find_drive_file(service,'bar_inventory_v3_latest.db',cfg['folder_id'])
        if not found: return
        request=service.files().get_media(fileId=found['id'])
        fh=io.FileIO(DB,'wb'); dl=MediaIoBaseDownload(fh,request); done=False
        while not done: _,done=dl.next_chunk()
        fh.close()
    except Exception:
        pass

restore_db_from_drive_if_missing()

# --------------------------- DB ---------------------------
@st.cache_resource
def db():
    c = sqlite3.connect(DB, check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c
con = db()

def q(sql, p=()): return con.execute(sql, p).fetchall()
def one(sql, p=()): return con.execute(sql, p).fetchone()
def ex(sql, p=()): con.execute(sql, p); con.commit(); backup_db_to_drive()

def now_iso(): return datetime.now().isoformat(timespec="seconds")
def hash_pin(pin): return hashlib.sha256(pin.encode()).hexdigest()

def init_db():
    con.executescript("""
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, pin_hash TEXT NOT NULL DEFAULT '', email TEXT UNIQUE,
      role TEXT NOT NULL CHECK(role IN ('STAFF','MANAGER','GENERAL_MANAGER','ADMIN')), active INTEGER DEFAULT 1,
      last_login_at TEXT, created_at TEXT);
    CREATE TABLE IF NOT EXISTS categories(
      id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, count_unit TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS products(
      id INTEGER PRIMARY KEY, category_id INTEGER NOT NULL, name TEXT NOT NULL,
      bottle_ml REAL, package_type TEXT DEFAULT 'Botella', active INTEGER DEFAULT 1, daily_inventory INTEGER DEFAULT 0,
      UNIQUE(name,bottle_ml,package_type), FOREIGN KEY(category_id) REFERENCES categories(id));
    CREATE TABLE IF NOT EXISTS locations(id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);
    CREATE TABLE IF NOT EXISTS inventory_sessions(
      id INTEGER PRIMARY KEY, session_date TEXT NOT NULL, session_type TEXT NOT NULL,
      user_id INTEGER, created_at TEXT NOT NULL, submitted INTEGER DEFAULT 1, notes TEXT, inventory_cycle TEXT DEFAULT 'DAILY',
      FOREIGN KEY(user_id) REFERENCES users(id));
    CREATE TABLE IF NOT EXISTS inventory_counts(
      id INTEGER PRIMARY KEY, session_id INTEGER NOT NULL, product_id INTEGER NOT NULL,
      location_id INTEGER NOT NULL, qty_base REAL NOT NULL, previous_qty REAL,
      variance REAL, observation TEXT,
      FOREIGN KEY(session_id) REFERENCES inventory_sessions(id),
      FOREIGN KEY(product_id) REFERENCES products(id), FOREIGN KEY(location_id) REFERENCES locations(id));
    CREATE TABLE IF NOT EXISTS movements(
      id INTEGER PRIMARY KEY, movement_date TEXT NOT NULL, movement_type TEXT NOT NULL,
      product_id INTEGER NOT NULL, qty_base REAL NOT NULL, from_location_id INTEGER,
      to_location_id INTEGER, user_id INTEGER, supplier TEXT, reference TEXT,
      observation TEXT, created_at TEXT NOT NULL,
      FOREIGN KEY(product_id) REFERENCES products(id));
    CREATE TABLE IF NOT EXISTS cocktails(id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, active INTEGER DEFAULT 1);
    CREATE TABLE IF NOT EXISTS recipes(
      id INTEGER PRIMARY KEY, cocktail_id INTEGER NOT NULL, product_id INTEGER NOT NULL,
      oz_qty REAL NOT NULL, UNIQUE(cocktail_id,product_id));
    CREATE TABLE IF NOT EXISTS pos_sales(
      id INTEGER PRIMARY KEY, sale_date TEXT NOT NULL, cocktail_id INTEGER, product_id INTEGER,
      sale_type TEXT NOT NULL, quantity REAL NOT NULL, oz_per_unit REAL,
      user_id INTEGER, observation TEXT, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS legacy_rows(
      id INTEGER PRIMARY KEY, source_sheet TEXT, source_row INTEGER, raw_text TEXT,
      imported_at TEXT NOT NULL);
    """)
    # Migración compatible desde bases anteriores: añade campos de autenticación Google si faltan.
    cols={r[1] for r in con.execute("PRAGMA table_info(users)").fetchall()}
    if "email" not in cols: con.execute("ALTER TABLE users ADD COLUMN email TEXT")
    if "last_login_at" not in cols: con.execute("ALTER TABLE users ADD COLUMN last_login_at TEXT")
    if "created_at" not in cols: con.execute("ALTER TABLE users ADD COLUMN created_at TEXT")
    pcols={r[1] for r in con.execute("PRAGMA table_info(products)").fetchall()}
    if "unit_cost" not in pcols: con.execute("ALTER TABLE products ADD COLUMN unit_cost REAL")
    try: con.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE email IS NOT NULL")
    except sqlite3.OperationalError: pass
    for n,u in [("Cerveza","bottle"),("Licor","oz"),("Cócteles","sale")]:
        con.execute("INSERT OR IGNORE INTO categories(name,count_unit) VALUES(?,?)", (n,u))
    for n in ["Bar","Bodega"]:
        con.execute("INSERT OR IGNORE INTO locations(name) VALUES(?)", (n,))
    if not one("SELECT 1 FROM users"):
        con.execute("INSERT INTO users(name,pin_hash,role,created_at) VALUES(?,?,?,?)", ("Admin","","ADMIN",now_iso()))
    defaults = {"safety_stock_pct":"15","tolerance_beer":"1","tolerance_liquor":"1"}
    for k,v in defaults.items(): con.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)",(k,v))
    con.commit()

init_db()

# V0.3.7 migration: new GENERAL_MANAGER role, inventory frequency and daily-liquor flags.
def ensure_v037_schema():
    # Existing V0.3.x databases have a CHECK constraint that does not include GENERAL_MANAGER.
    # Rebuild only the users table while preserving IDs so all historical references remain valid.
    row=one("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
    users_sql=(row['sql'] if row and row['sql'] else '')
    if 'GENERAL_MANAGER' not in users_sql:
        con.commit()
        con.execute("PRAGMA foreign_keys=OFF")
        try:
            con.execute("BEGIN")
            con.execute("""CREATE TABLE users_new(
              id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, pin_hash TEXT NOT NULL DEFAULT '', email TEXT UNIQUE,
              role TEXT NOT NULL CHECK(role IN ('STAFF','MANAGER','GENERAL_MANAGER','ADMIN')), active INTEGER DEFAULT 1,
              last_login_at TEXT, created_at TEXT)""")
            con.execute("""INSERT INTO users_new(id,name,pin_hash,email,role,active,last_login_at,created_at)
                           SELECT id,name,COALESCE(pin_hash,''),email,role,active,last_login_at,created_at FROM users""")
            con.execute("DROP TABLE users")
            con.execute("ALTER TABLE users_new RENAME TO users")
            con.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE email IS NOT NULL")
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.execute("PRAGMA foreign_keys=ON")

    pcols={r[1] for r in con.execute("PRAGMA table_info(products)").fetchall()}
    if 'daily_inventory' not in pcols:
        con.execute("ALTER TABLE products ADD COLUMN daily_inventory INTEGER DEFAULT 0")

    scols={r[1] for r in con.execute("PRAGMA table_info(inventory_sessions)").fetchall()}
    if 'inventory_cycle' not in scols:
        con.execute("ALTER TABLE inventory_sessions ADD COLUMN inventory_cycle TEXT DEFAULT 'DAILY'")

    con.commit()

ensure_v037_schema()

# V0.3.4 migration: preserve bottle-equivalent counts when ml is still pending.
def ensure_v033_schema():
    cols={r[1] for r in con.execute("PRAGMA table_info(inventory_counts)").fetchall()}
    if 'qty_bottle_equiv' not in cols: con.execute("ALTER TABLE inventory_counts ADD COLUMN qty_bottle_equiv REAL")
    mcols={r[1] for r in con.execute("PRAGMA table_info(movements)").fetchall()}
    if 'qty_bottle_equiv' not in mcols: con.execute("ALTER TABLE movements ADD COLUMN qty_bottle_equiv REAL")
    con.commit()
ensure_v033_schema()

# ---------------------- catalog seed from current sheet ----------------------
BEERS = ["Corona","Corona Sunbrew","XX","Negra","Especial","Sol","Coors","Molson"]
LIQUORS = [
"Jose Cuervo Silver","Jose Cuervo Gold","1800 Cristalino","Jose Cuervo Tradicional Plata","Patron Silver",
"Patron Reposado","Patron Añejo","Casamigos Añejo","Casamigos Blanco","Casamigos Reposado","Don Julio Añejo",
"Don Julio Reposado","Don Julio Blanco","Patron Cristalino","Don Julio 70","Don Julio 1942","Reserva Extra Añejo",
"1800 Blanco","1800 Reposado","1800 Coco","Herradura","Los Arango","Casa Azul","Mezcal Ilegal","Mezcal Vida",
"Mezcal Don Ramon","Mezcal Zapata","Captain Morgan White","Captain Morgan Dark","Havana Club","Triple Sec McGuinness",
"Grand Marnier","Baileys","Blue Curacao","Aperol","Crema de Cacao","Canton Ginger Liqueur","Bombay Gin","Gin True",
"Vodka True","Absolut Vodka","Grey Goose Vodka","Hendrick's Gin","Johnnie Walker Black Label","Crown Royal","Cachaça",
"Disaronno","Piña Jalapeño Tequila","Cabernet Sauvignon","Pinot Noir","Merlot","Sauvignon Blanc","Chardonnay","Pinot Grigio"
]

def seed_catalog():
    if one("SELECT COUNT(*) n FROM products")["n"] > 0: return
    cid_beer = one("SELECT id FROM categories WHERE name='Cerveza'")["id"]
    cid_liq = one("SELECT id FROM categories WHERE name='Licor'")["id"]
    for n in BEERS: con.execute("INSERT OR IGNORE INTO products(category_id,name,bottle_ml,package_type) VALUES(?,?,NULL,'Botella')",(cid_beer,n))
    for n in LIQUORS: con.execute("INSERT OR IGNORE INTO products(category_id,name,bottle_ml,package_type) VALUES(?,?,NULL,'Botella')",(cid_liq,n))
    con.commit()
seed_catalog()

def seed_daily_inventory_defaults():
    """Mark the current seven main liquors once; admins can change this list later."""
    if one("SELECT value FROM settings WHERE key='daily_inventory_defaults_seeded'"):
        return
    principal=[
        'Jose Cuervo Silver','Jose Cuervo Gold','Triple Sec McGuinness','Mezcal Ilegal',
        'Captain Morgan Dark','Captain Morgan White','Vodka True'
    ]
    for name in principal:
        con.execute("UPDATE products SET daily_inventory=1 WHERE lower(name)=lower(?)",(name,))
    con.execute("INSERT INTO settings(key,value) VALUES('daily_inventory_defaults_seeded','1')")
    con.commit()
seed_daily_inventory_defaults()

def seed_sheet_history():
    """Carga una sola vez los registros históricos que pueden interpretarse con suficiente certeza
    del Google Sheet recibido (agosto 2026). No fuerza interpretaciones sobre filas ambiguas."""
    if one("SELECT value FROM settings WHERE key='sheet_history_seeded'"):
        return
    admin=one("SELECT id FROM users WHERE name='Admin'")['id']
    bar=one("SELECT id FROM locations WHERE name='Bar'")['id']
    def pid(name):
        r=one("SELECT id FROM products WHERE lower(name)=lower(?) ORDER BY id LIMIT 1",(name,))
        return r['id'] if r else None
    def session(ds,kind,items):
        cur=con.execute("INSERT INTO inventory_sessions(session_date,session_type,user_id,created_at,notes) VALUES(?,?,?,?,?)",
                        (ds,kind,admin,f"{ds}T23:00:00","Importado del Google Sheet recibido"))
        sid=cur.lastrowid
        for name,qty in items.items():
            x=pid(name)
            if x is not None:
                con.execute("INSERT INTO inventory_counts(session_id,product_id,location_id,qty_base) VALUES(?,?,?,?)",(sid,x,bar,float(qty)))
    # Cervezas: el archivo contiene conteo inicial/final explícito. Se conserva el físico,
    # aunque alguna fórmula manual del Sheet sea inconsistente; la V0.2 recalcula desde los conteos.
    beer_days={
      '2026-08-21':({'Corona':132,'Corona Sunbrew':34,'XX':45,'Negra':27,'Especial':26,'Sol':57,'Coors':32,'Molson':15},{'Corona':112,'Corona Sunbrew':33,'XX':45,'Negra':25,'Especial':17,'Sol':55,'Coors':28,'Molson':15}),
      '2026-08-22':({'Corona':112,'Corona Sunbrew':33,'XX':45,'Negra':27,'Especial':20,'Sol':55,'Coors':28,'Molson':15},{'Corona':103,'Corona Sunbrew':30,'XX':40,'Negra':17,'Especial':2,'Sol':53,'Coors':27,'Molson':15}),
      '2026-08-23':({'Corona':103,'Corona Sunbrew':30,'XX':40,'Negra':17,'Especial':2,'Sol':53,'Coors':27,'Molson':15},{'Corona':96,'Corona Sunbrew':28,'XX':39,'Negra':15,'Especial':1,'Sol':51,'Coors':27,'Molson':15}),
      '2026-08-24':({'Corona':96,'Corona Sunbrew':28,'XX':39,'Negra':15,'Especial':1,'Sol':51,'Coors':26,'Molson':15},{'Corona':89,'Corona Sunbrew':27,'XX':28,'Negra':12,'Especial':0,'Sol':48,'Coors':26,'Molson':9}),
      '2026-08-25':({'Corona':89,'Corona Sunbrew':27,'XX':32,'Negra':12,'Especial':0,'Sol':48,'Coors':26,'Molson':9},{'Corona':83,'Corona Sunbrew':25,'XX':28,'Negra':8,'Especial':0,'Sol':41,'Coors':26,'Molson':7}),
      '2026-08-26':({'Corona':83,'Corona Sunbrew':26,'XX':30,'Negra':8,'Especial':0,'Sol':50,'Coors':26,'Molson':7},{'Corona':83,'Corona Sunbrew':23,'XX':30,'Negra':6,'Especial':0,'Sol':48,'Coors':25,'Molson':7}),
      '2026-08-27':({'Corona':83,'Corona Sunbrew':23,'XX':29,'Negra':6,'Especial':0,'Sol':48,'Coors':25,'Molson':7},{'Corona':78,'Corona Sunbrew':23,'XX':21,'Negra':4,'Especial':0,'Sol':47,'Coors':23,'Molson':6}),
      '2026-08-28':({'Corona':78,'Corona Sunbrew':23,'XX':21,'Negra':4,'Especial':0,'Sol':47,'Coors':23,'Molson':6},{'Corona':120,'Corona Sunbrew':23,'XX':8,'Negra':0,'Especial':0,'Sol':46,'Coors':23,'Molson':5}),
    }
    for ds,(op,cl) in beer_days.items(): session(ds,'OPENING',op); session(ds,'CLOSING',cl)
    # 29 de agosto solo tiene conteo inicial en el archivo.
    session('2026-08-29','OPENING',{'Corona':114,'Corona Sunbrew':23,'XX':28,'Negra':24,'Especial':0,'Sol':45,'Coors':45,'Molson':5})
    # POS de cervezas disponible explícitamente en el Sheet.
    beer_pos={
      '2026-08-22':{'Corona':6,'Corona Sunbrew':3,'XX':0,'Negra':7,'Especial':8,'Sol':2,'Coors':1,'Molson':0},
      '2026-08-23':{'Corona':7,'Corona Sunbrew':2,'XX':2,'Negra':1,'Especial':1,'Sol':2,'Coors':0,'Molson':0},
      '2026-08-24':{'Corona':7,'Corona Sunbrew':1,'XX':6,'Negra':3,'Especial':1,'Sol':3,'Coors':0,'Molson':6},
      '2026-08-25':{'Corona':6,'Corona Sunbrew':2,'XX':0,'Negra':4,'Especial':0,'Sol':0,'Coors':0,'Molson':2},
      '2026-08-26':{'Corona':0,'Corona Sunbrew':2,'XX':0,'Negra':2,'Especial':0,'Sol':2,'Coors':1,'Molson':0},
    }
    for ds,items in beer_pos.items():
        for name,qty in items.items():
            x=pid(name)
            if x is not None:
                con.execute("INSERT INTO pos_sales(sale_date,product_id,sale_type,quantity,user_id,created_at,observation) VALUES(?,?,?,?,?,?,?)",
                            (ds,x,'Cerveza',float(qty),admin,f"{ds}T23:30:00",'Importado del Google Sheet'))
    # Licores: se importan únicamente filas donde la interpretación apertura/cierre es razonablemente clara.
    liq22_open={'Jose Cuervo Silver':220.5,'Jose Cuervo Gold':204,'Triple Sec McGuinness':181.5,'Captain Morgan Dark':86.5,'Captain Morgan White':67.8,'Mezcal Ilegal':39.1}
    liq22_close={'Jose Cuervo Silver':136,'Jose Cuervo Gold':204,'Triple Sec McGuinness':157.3,'Captain Morgan Dark':84,'Captain Morgan White':51,'Mezcal Ilegal':39.1}
    session('2026-08-22','OPENING',liq22_open); session('2026-08-22','CLOSING',liq22_close)
    liq23_open={'Jose Cuervo Silver':136,'Jose Cuervo Gold':204,'Triple Sec McGuinness':157.3,'Captain Morgan Dark':84,'Captain Morgan White':51,'Mezcal Ilegal':39.1}
    liq23_close={'Jose Cuervo Silver':85,'Jose Cuervo Gold':204,'Triple Sec McGuinness':141.5,'Captain Morgan Dark':88.5,'Captain Morgan White':40.8,'Mezcal Ilegal':38.4}
    session('2026-08-23','OPENING',liq23_open); session('2026-08-23','CLOSING',liq23_close)
    session('2026-08-24','OPENING',{'Jose Cuervo Silver':51,'Jose Cuervo Gold':204,'Triple Sec McGuinness':124.2,'Captain Morgan Dark':60,'Captain Morgan White':37.4,'Mezcal Ilegal':32.2})
    # Las demás filas se conservan como nota de procedencia, sin convertirlas en movimientos inventados.
    con.execute("INSERT INTO legacy_rows(source_sheet,source_row,raw_text,imported_at) VALUES(?,?,?,?)",
                ('INVENTARIO DIARIO',2,'Filas iniciales del día 21 contienen inventario/entradas pero no cierre completo; conservadas para revisión manual.',now_iso()))
    con.execute("INSERT INTO settings(key,value) VALUES('sheet_history_seeded','1')")
    con.commit()
seed_sheet_history()

# --------------------------- helpers ---------------------------
def setting(k, default):
    r=one("SELECT value FROM settings WHERE key=?",(k,)); return r["value"] if r else default

def products(cat=None, active=True):
    sql="SELECT p.*,c.name category,c.count_unit FROM products p JOIN categories c ON c.id=p.category_id WHERE 1=1"; ps=[]
    if active: sql += " AND p.active=1"
    if cat: sql += " AND c.name=?"; ps.append(cat)
    return q(sql+" ORDER BY c.name,p.name,COALESCE(p.bottle_ml,0)",ps)

def inventory_products(cycle='DAILY'):
    """Products required for the selected physical inventory cycle.
    DAILY = all beers + main liquors. WEEKLY = all beers + all liquors.
    """
    all_items=[p for p in products() if p['category'] in ('Cerveza','Licor')]
    if cycle=='WEEKLY':
        return all_items
    return [p for p in all_items if p['category']=='Cerveza' or int(p['daily_inventory'] or 0)==1]

def latest_opening_cycle(ds):
    r=one("""SELECT COALESCE(inventory_cycle,'DAILY') cycle FROM inventory_sessions
             WHERE session_date=? AND session_type='OPENING' ORDER BY created_at DESC LIMIT 1""",(ds,))
    return str(r['cycle']) if r else None

ROLE_LABELS={'STAFF':'STAFF','MANAGER':'MANAGER','GENERAL_MANAGER':'MANAGER GENERAL','ADMIN':'ADMIN'}

def product_label(p):
    ml = f" · {int(p['bottle_ml'])} ml" if p['bottle_ml'] else ""
    pkg = f" · {p['package_type']}" if p['package_type'] and p['package_type'] != 'Botella' else ""
    return f"{p['name']}{ml}{pkg}"

def unit_label(p): return "botellas" if p['category']=="Cerveza" else "oz"

def qty_fmt(p, v):
    if v is None: return "—"
    return f"{v:.0f} botellas" if p['category']=="Cerveza" else f"{v:.2f} oz"

def last_close(pid, lid, before_or_on=None):
    sql="""SELECT ic.qty_base,s.session_date,s.created_at FROM inventory_counts ic
           JOIN inventory_sessions s ON s.id=ic.session_id
           WHERE ic.product_id=? AND ic.location_id=? AND s.session_type='CLOSING'"""
    ps=[pid,lid]
    if before_or_on: sql += " AND s.session_date<=?"; ps.append(before_or_on)
    sql += " ORDER BY s.session_date DESC,s.created_at DESC LIMIT 1"
    r=one(sql,ps); return (float(r['qty_base']),r['session_date']) if r else (None,None)

def save_session(kind, counts, session_date=None, notes="", inventory_cycle="DAILY"):
    d=(session_date or date.today()).isoformat() if hasattr((session_date or date.today()),'isoformat') else str(session_date)
    cur=con.execute("INSERT INTO inventory_sessions(session_date,session_type,user_id,created_at,notes,inventory_cycle) VALUES(?,?,?,?,?,?)",
                    (d,kind,user['id'],now_iso(),notes,inventory_cycle)); sid=cur.lastrowid
    for x in counts:
        con.execute("""INSERT INTO inventory_counts(session_id,product_id,location_id,qty_base,previous_qty,variance,observation,qty_bottle_equiv)
                       VALUES(?,?,?,?,?,?,?,?)""",(sid,x['pid'],x['lid'],x['qty'],x.get('prev'),x.get('var'),x.get('obs'),x.get('bottle_equiv')))
    con.commit(); backup_db_to_drive(); return sid

def bottle_count_input(p, key, default_base=0.0, default_bottles=None):
    if p['category']=='Cerveza':
        units=float(st.number_input("Unidades / botellas",min_value=0,value=int(round(max(float(default_base or 0),0))),step=1,key=key+'u'))
        return {'base':units,'bottles':None}
    boz=bottle_oz(p)
    if default_bottles is None:
        default_bottles=(max(float(default_base or 0),0)/boz) if boz else 0.0
    default_bottles=max(float(default_bottles or 0),0)
    full=int(math.floor(default_bottles+1e-9)); frac_raw=max(0.0,min(default_bottles-full,.99))
    fractions=[0.0,0.25,0.50,0.75]; frac=min(fractions,key=lambda x:abs(x-frac_raw))
    c1,c2=st.columns([1.2,1])
    full_val=int(c1.number_input("Botellas completas",min_value=0,value=full,step=1,key=key+'f'))
    frac_val=float(c2.selectbox("Fracción botella abierta",fractions,index=fractions.index(frac),format_func=lambda x:{0.0:'0 (sin abierta)',0.25:'0.25 · ¼',0.5:'0.50 · ½',0.75:'0.75 · ¾'}[x],key=key+'q'))
    bottle_equiv=full_val+frac_val
    if boz:
        total_oz=bottle_equiv*boz
        st.caption(f"Conteo: {bottle_equiv:.2f} botellas · {p['bottle_ml']:.0f} ml/botella · Total calculado: {total_oz:.2f} oz")
        return {'base':total_oz,'bottles':bottle_equiv}
    st.info(f"Conteo guardado: {bottle_equiv:.2f} botellas. La presentación en ml está pendiente; las oz se calcularán automáticamente cuando el ADMIN registre los ml.")
    return {'base':0.0,'bottles':bottle_equiv}

def last_close_detail(pid,lid,before_or_on=None):
    sql="""SELECT ic.qty_base,ic.qty_bottle_equiv,s.session_date,s.created_at FROM inventory_counts ic
           JOIN inventory_sessions s ON s.id=ic.session_id
           WHERE ic.product_id=? AND ic.location_id=? AND s.session_type='CLOSING'"""
    ps=[pid,lid]
    if before_or_on: sql += " AND s.session_date<=?"; ps.append(before_or_on)
    sql += " ORDER BY s.session_date DESC,s.created_at DESC LIMIT 1"
    r=one(sql,ps)
    return (float(r['qty_base']), float(r['qty_bottle_equiv']) if r['qty_bottle_equiv'] is not None else None, r['session_date']) if r else (None,None,None)

def session_qty_detail(d,pid,kind,lid):
    r=one("""SELECT ic.qty_base,ic.qty_bottle_equiv FROM inventory_counts ic JOIN inventory_sessions s ON s.id=ic.session_id
             WHERE s.session_date=? AND s.session_type=? AND ic.product_id=? AND ic.location_id=?
             ORDER BY s.created_at DESC LIMIT 1""",(d,kind,pid,lid))
    return (float(r['qty_base']), float(r['qty_bottle_equiv']) if r['qty_bottle_equiv'] is not None else None) if r else (None,None)

def backfill_product_bottle_counts(pid):
    p=one("SELECT p.*,c.name category FROM products p JOIN categories c ON c.id=p.category_id WHERE p.id=?",(pid,))
    if not p or p['category']!='Licor' or not p['bottle_ml']:
        return
    boz=float(p['bottle_ml'])/ML_PER_OZ
    con.execute("UPDATE inventory_counts SET qty_base=qty_bottle_equiv*? WHERE product_id=? AND qty_bottle_equiv IS NOT NULL",(boz,pid))
    con.execute("UPDATE movements SET qty_base=qty_bottle_equiv*? WHERE product_id=? AND qty_bottle_equiv IS NOT NULL",(boz,pid))
    con.commit(); backup_db_to_drive()

def movement_qty_input(p,key,label="Cantidad"):
    if p['category']=='Cerveza':
        units=float(st.number_input(f"{label} · unidades / botellas",min_value=0,value=0,step=1,key=key+'u'))
        return {'base':units,'bottles':None}
    fractions=[0.0,0.25,0.50,0.75]
    c1,c2=st.columns([1.2,1])
    full=int(c1.number_input(f"{label} · botellas completas",min_value=0,value=0,step=1,key=key+'f'))
    frac=float(c2.selectbox("Fracción botella abierta",fractions,index=0,format_func=lambda x:{0.0:'0 (sin abierta)',0.25:'0.25 · ¼',0.5:'0.50 · ½',0.75:'0.75 · ¾'}[x],key=key+'q'))
    bottles=full+frac; boz=bottle_oz(p)
    if boz:
        base=bottles*boz; st.caption(f"Movimiento: {bottles:.2f} botellas · {p['bottle_ml']:.0f} ml/botella · {base:.2f} oz")
    else:
        base=0.0
        if bottles>0: st.caption(f"Movimiento: {bottles:.2f} botellas · ml pendiente; se convertirán a oz cuando se complete la presentación.")
    return {'base':base,'bottles':bottles}

def create_movement(typ,pid,qty,from_id=None,to_id=None,supplier=None,reference=None,obs="",d=None,bottle_equiv=None):
    con.execute("""INSERT INTO movements(movement_date,movement_type,product_id,qty_base,from_location_id,to_location_id,user_id,supplier,reference,observation,created_at,qty_bottle_equiv)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",((d or date.today()).isoformat(),typ,pid,qty,from_id,to_id,user['id'],supplier,reference,obs,now_iso(),bottle_equiv))
    con.commit(); backup_db_to_drive()

def session_qty(d, pid, kind, lid):
    r=one("""SELECT ic.qty_base FROM inventory_counts ic JOIN inventory_sessions s ON s.id=ic.session_id
             WHERE s.session_date=? AND s.session_type=? AND ic.product_id=? AND ic.location_id=?
             ORDER BY s.created_at DESC LIMIT 1""",(d,kind,pid,lid))
    return float(r['qty_base']) if r else None

def transfers_in(d,pid,bar_id):
    r=one("SELECT COALESCE(SUM(qty_base),0) x FROM movements WHERE movement_date=? AND product_id=? AND to_location_id=? AND movement_type IN ('TRANSFER','SUPPLIER')",(d,pid,bar_id))
    return float(r['x'] or 0)

def adjustments(d,pid,bar_id):
    r=one("SELECT COALESCE(SUM(qty_base),0) x FROM movements WHERE movement_date=? AND product_id=? AND from_location_id=? AND movement_type IN ('PRUEBA','DESPERDICIO','CORTESIA')",(d,pid,bar_id))
    return float(r['x'] or 0)

def expected_sales(d,pid,p):
    total=0.0
    # Direct product sales: beer count = bottles, liquor uses oz_per_unit when provided; bottle liquor converts ml when known.
    rows=q("SELECT sale_type,quantity,oz_per_unit FROM pos_sales WHERE sale_date=? AND product_id=?",(d,pid))
    for r in rows:
        if p['category']=='Cerveza': total += float(r['quantity'])
        elif r['oz_per_unit'] is not None: total += float(r['quantity'])*float(r['oz_per_unit'])
        elif r['sale_type']=='Botella de licor' and p['bottle_ml']: total += float(r['quantity'])*(float(p['bottle_ml'])/ML_PER_OZ)
    # Cocktail recipes
    rr=q("""SELECT ps.quantity,r.oz_qty FROM pos_sales ps JOIN recipes r ON r.cocktail_id=ps.cocktail_id
            WHERE ps.sale_date=? AND r.product_id=?""",(d,pid))
    total += sum(float(x['quantity'])*float(x['oz_qty']) for x in rr)
    return total

def opening_variance(d,pid,bar_id):
    r=one("""SELECT ic.variance FROM inventory_counts ic JOIN inventory_sessions s ON s.id=ic.session_id
             WHERE s.session_date=? AND s.session_type='OPENING' AND ic.product_id=? AND ic.location_id=?
             ORDER BY s.created_at DESC LIMIT 1""",(d,pid,bar_id))
    return float(r['variance']) if r and r['variance'] is not None else None

def date_range(d1,d2):
    cur=d1
    while cur<=d2:
        yield cur
        cur += timedelta(days=1)

def consolidated(d1,d2):
    bar=one("SELECT id FROM locations WHERE name='Bar'")['id']
    rows=[]
    for p in products():
        if p['category'] not in ('Cerveza','Licor'): continue
        real=expected=adj=trans=0.0; days_complete=0; open_alerts=0; open_var_sum=0.0
        first_open=last_close_val=None
        for dd in date_range(d1,d2):
            ds=dd.isoformat(); op=session_qty(ds,p['id'],'OPENING',bar); cl=session_qty(ds,p['id'],'CLOSING',bar)
            ti=transfers_in(ds,p['id'],bar); av=adjustments(ds,p['id'],bar); ev=expected_sales(ds,p['id'],p)
            expected += ev; adj += av; trans += ti
            if op is not None and first_open is None: first_open=op
            if cl is not None: last_close_val=cl
            if op is not None and cl is not None:
                real += op + ti - cl; days_complete += 1
            ov=opening_variance(ds,p['id'],bar)
            tol=float(setting('tolerance_beer','1')) if p['category']=='Cerveza' else float(setting('tolerance_liquor','1'))
            if ov is not None and abs(ov)>tol: open_alerts += 1; open_var_sum += ov
        explained=expected+adj; diff=real-explained
        tol=float(setting('tolerance_beer','1')) if p['category']=='Cerveza' else float(setting('tolerance_liquor','1'))
        status='✅ OK' if abs(diff)<=tol and open_alerts==0 else ('🔴 Revisar' if abs(diff)>tol*3 or open_alerts>=2 else '⚠️ Revisar')
        rows.append({
            'Producto':product_label(p),'Categoría':p['category'],'Inicial':first_open,'Final':last_close_val,
            'Entradas al bar':trans,'Consumo real':real,'Consumo esperado':expected,'Ajustes':adj,
            'Diferencia no explicada':diff,'Alertas apertura':open_alerts,'Estado':status,'Días completos':days_complete,
            '_pid':p['id'],'_unit':unit_label(p),'_p':p
        })
    return rows

def current_stock(pid, location_id):
    # Best physical count if available, otherwise movement-derived stock from 0.
    r=one("""SELECT ic.qty_base,s.session_date,s.created_at FROM inventory_counts ic JOIN inventory_sessions s ON s.id=ic.session_id
             WHERE ic.product_id=? AND ic.location_id=? ORDER BY s.session_date DESC,s.created_at DESC LIMIT 1""",(pid,location_id))
    base=float(r['qty_base']) if r else 0.0; base_date=r['session_date'] if r else '1900-01-01'
    incoming=one("SELECT COALESCE(SUM(qty_base),0) x FROM movements WHERE product_id=? AND to_location_id=? AND movement_date>?",(pid,location_id,base_date))['x']
    outgoing=one("SELECT COALESCE(SUM(qty_base),0) x FROM movements WHERE product_id=? AND from_location_id=? AND movement_date>?",(pid,location_id,base_date))['x']
    return base + float(incoming or 0)-float(outgoing or 0)

def bottle_oz(p):
    return (float(p['bottle_ml'])/ML_PER_OZ) if p['category']=='Licor' and p['bottle_ml'] else None

def oz_and_bottles_text(p, qty, beer_label='unid'):
    qty=max(float(qty or 0),0)
    if p['category']=='Cerveza':
        return f"{qty:.0f} {beer_label}"
    boz=bottle_oz(p)
    if not boz:
        return f"{qty:.2f} oz\n⚠ Falta ml"
    return f"{qty:.2f} oz\n{qty/boz:.2f} bot"

def difference_cost(r):
    p=r['_p']; cost=p['unit_cost']
    if cost is None: return None
    diff=abs(float(r['Diferencia no explicada'] or 0))
    if p['category']=='Cerveza': return diff*float(cost)
    boz=bottle_oz(p)
    return (diff/boz*float(cost)) if boz else None

def product_accuracy(r):
    real=abs(float(r['Consumo real'] or 0)); diff=abs(float(r['Diferencia no explicada'] or 0))
    if real<=0: return None
    return max(0.0,min(100.0,(1.0-diff/real)*100.0))

def daily_trend(d1,d2,category):
    bar=one("SELECT id FROM locations WHERE name='Bar'")['id']
    out=[]
    for dd in date_range(d1,d2):
        real=expected=0.0; complete=False
        for p in products(category):
            op=session_qty(dd.isoformat(),p['id'],'OPENING',bar); cl=session_qty(dd.isoformat(),p['id'],'CLOSING',bar)
            if op is not None and cl is not None:
                real += op + transfers_in(dd.isoformat(),p['id'],bar) - cl
                complete=True
            expected += expected_sales(dd.isoformat(),p['id'],p)
        if complete or expected>0:
            out.append({'Fecha':dd.isoformat(),'Consumo real':max(real,0),'Consumo esperado':max(expected,0)})
    return pd.DataFrame(out)

# --------------------------- Google authentication ---------------------------
def secret_value(section, key, default=""):
    try:
        return str(st.secrets[section][key]).strip()
    except Exception:
        return default

def normalized_email(v): return (v or "").strip().lower()

def google_identity():
    if not st.user.is_logged_in:
        return None
    try:
        return {"email": normalized_email(st.user.email), "name": str(st.user.name or "").strip()}
    except Exception:
        return None

def bootstrap_admin(identity):
    """Autoriza automáticamente solo el correo ADMIN configurado en Secrets.
    Esto permite arrancar V0.3 sin dejar un registro público ni un PIN compartido."""
    admin_email=normalized_email(secret_value("app","bootstrap_admin_email"))
    if not identity or not admin_email or identity["email"] != admin_email:
        return
    u=one("SELECT * FROM users WHERE lower(email)=?",(admin_email,))
    if u:
        ex("UPDATE users SET active=1,role='ADMIN',last_login_at=? WHERE id=?",(now_iso(),u['id']))
        return
    legacy=one("SELECT * FROM users WHERE name='Admin' AND (email IS NULL OR email='') ORDER BY id LIMIT 1")
    if legacy:
        ex("UPDATE users SET email=?,name=?,role='ADMIN',active=1,last_login_at=?,created_at=COALESCE(created_at,?) WHERE id=?",
           (admin_email,identity['name'] or 'Admin',now_iso(),now_iso(),legacy['id']))
    else:
        ex("INSERT INTO users(name,pin_hash,email,role,active,last_login_at,created_at) VALUES(?,?,?,?,1,?,?)",
           (identity['name'] or admin_email,'',admin_email,'ADMIN',now_iso(),now_iso()))

def login_screen():
    st.markdown('<div class="ramona-login-wrap">', unsafe_allow_html=True)
    st.image(LOGO_PATH, width=320)
    st.markdown("## Inventario La Ramona")
    st.caption("Control de inventario · V0.3.7 · Acceso seguro con Google")
    st.write("Inicia sesión con la cuenta de Google autorizada por el administrador.")
    st.button("Continuar con Google",type="primary",width="stretch",on_click=st.login)
    st.caption("Tener el enlace de la aplicación no concede acceso. El correo debe estar autorizado y activo.")
    st.markdown('</div>', unsafe_allow_html=True)

if not st.user.is_logged_in:
    login_screen(); st.stop()

identity=google_identity()
bootstrap_admin(identity)
user_row=one("SELECT * FROM users WHERE lower(email)=?",(identity['email'],)) if identity else None
if not user_row or not user_row['active']:
    page_header("Acceso no autorizado", "La cuenta actual no tiene permisos activos para usar el sistema.")
    if identity:
        st.write(f"La cuenta **{identity['email']}** no tiene acceso activo a Inventario La Ramona.")
    st.caption("Solicita al administrador que autorice o reactive este correo.")
    st.button("Cerrar sesión",width="stretch",on_click=st.logout)
    st.stop()

user=dict(user_row)
ex("UPDATE users SET last_login_at=? WHERE id=?",(now_iso(),user['id']))

with st.sidebar:
    st.image(LOGO_PATH, width=185)
    st.markdown("---")
    st.markdown(f"**{user['name']}**")
    st.caption(f"{ROLE_LABELS.get(user['role'],user['role'])} · {user['email']}")
    if user['role'] in ('MANAGER','GENERAL_MANAGER','ADMIN'):
        pages=['Dashboard','Apertura','Cierre','Abastecimiento','POS / Ventas','Recibir pedido','Trasladar productos','Reporte PDF']
    else:
        pages=['Apertura','Cierre','Recibir pedido','Trasladar productos']
    if user['role'] in ('GENERAL_MANAGER','ADMIN'):
        pages += ['Administración']
    icons={'Dashboard':'▦','Apertura':'↑','Cierre':'↓','Abastecimiento':'🛒','POS / Ventas':'▤','Recibir pedido':'📦','Trasladar productos':'↔','Reporte PDF':'▥','Administración':'⚙'}
    display=[f"{icons.get(p,'•')}  {p}" for p in pages]
    selected=st.radio("Navegación",display,label_visibility="collapsed")
    page=pages[display.index(selected)]
    st.markdown("---")
    if st.button("Cerrar sesión",width="stretch"): st.logout()

# --------------------------- pages ---------------------------
if page=='Apertura':
    page_header("Apertura", "Conteo inicial del turno con inventario diario o semanal.")
    d=st.date_input("Fecha de apertura",value=date.today())
    cycle_label=st.radio("Tipo de inventario",['Diario','Semanal'],horizontal=True,key='opening_cycle')
    cycle='DAILY' if cycle_label=='Diario' else 'WEEKLY'
    if cycle=='DAILY':
        st.caption("Inventario diario: todas las cervezas + licores principales. Los demás licores quedan fuera para agilizar el conteo.")
    else:
        st.caption("Inventario semanal: todas las cervezas + todos los licores activos.")
    st.caption("Si no existe un cierre anterior comparable, el conteo se guarda como referencia sin generar una alerta falsa.")
    bar=one("SELECT id FROM locations WHERE name='Bar'")['id']; ps=inventory_products(cycle)
    counts=[]; missing_obs=False
    for cat in ['Cerveza','Licor']:
        g=[p for p in ps if p['category']==cat]
        if g: st.subheader(cat)
        for p in g:
            prev,prev_bottles,prev_date=last_close_detail(p['id'],bar,d.isoformat())
            with st.expander(product_label(p),expanded=True):
                # Secondary liquors are only counted weekly. Their prior weekly close is a reference,
                # not a same-day continuity check, because sales occurred during the interval.
                weekly_secondary=(cycle=='WEEKLY' and cat=='Licor' and int(p['daily_inventory'] or 0)==0)
                if prev is None:
                    st.info("Primer inventario registrado para este producto. No existe cierre anterior para comparar.")
                    res=bottle_count_input(p,f"op_{cycle}_{d}_{p['id']}",0); val=res['base']; var=None; obs=''; bottle_equiv=res['bottles']
                else:
                    if cat=='Licor' and not p['bottle_ml'] and prev_bottles is not None:
                        st.caption(f"Último cierre ({prev_date}): **{prev_bottles:.2f} botellas** · ml pendiente")
                    else:
                        st.caption(f"Último cierre ({prev_date}): **{qty_fmt(p,prev)}**")
                    res=bottle_count_input(p,f"op_{cycle}_{d}_{p['id']}",prev,prev_bottles); val=res['base']; bottle_equiv=res['bottles']; obs=''
                    if weekly_secondary:
                        var=None
                        st.caption("Licor de inventario semanal: el cierre anterior se muestra solo como referencia y no genera alerta automática por el intervalo entre conteos.")
                    else:
                        if cat=='Licor' and not p['bottle_ml']:
                            var=(bottle_equiv-prev_bottles) if prev_bottles is not None else None; tol=.25; var_unit='botellas'
                        else:
                            var=val-prev; tol=float(setting('tolerance_beer','1')) if cat=='Cerveza' else float(setting('tolerance_liquor','1')); var_unit=unit_label(p)
                        if var is not None and abs(var)>tol:
                            st.warning(f"Diferencia contra cierre anterior: {var:+.2f} {var_unit}")
                            obs=st.text_input("Observación obligatoria",key=f"opobs_{cycle}_{d}_{p['id']}")
                            missing_obs |= not bool(obs.strip())
                        elif var is not None: st.caption(f"Diferencia: {var:+.2f} {var_unit} · dentro de tolerancia")
                counts.append({'pid':p['id'],'lid':bar,'qty':val,'prev':prev,'var':var,'obs':obs,'bottle_equiv':bottle_equiv})
    st.info(f"Productos a contar: {len(ps)} · Tipo: {cycle_label}")
    if st.button("Guardar apertura",type="primary",width="stretch"):
        if missing_obs: st.error("Falta explicar una diferencia marcada como alerta.")
        else:
            save_session('OPENING',counts,d,inventory_cycle=cycle)
            st.success(f"Apertura {cycle_label.lower()} guardada correctamente.")

elif page=='Cierre':
    page_header("Cierre", "Conteo final con inventario diario o semanal y movimientos pendientes.")
    d=st.date_input("Fecha de cierre",value=date.today())
    detected=latest_opening_cycle(d.isoformat())
    options=['Diario','Semanal']; default_idx=1 if detected=='WEEKLY' else 0
    cycle_label=st.radio("Tipo de inventario",options,index=default_idx,horizontal=True,key='closing_cycle')
    cycle='DAILY' if cycle_label=='Diario' else 'WEEKLY'
    if detected and cycle!=detected:
        st.warning(f"La apertura más reciente de esta fecha fue {'semanal' if detected=='WEEKLY' else 'diaria'}. Revisa el tipo de inventario antes de guardar el cierre.")
    if cycle=='DAILY':
        st.caption("Inventario diario: todas las cervezas + licores principales.")
    else:
        st.caption("Inventario semanal: todas las cervezas + todos los licores activos.")
    bar=one("SELECT id FROM locations WHERE name='Bar'")['id']; wh=one("SELECT id FROM locations WHERE name='Bodega'")['id']
    ps=inventory_products(cycle); all_ps=[p for p in products() if p['category'] in ('Cerveza','Licor')]
    counts=[]
    for cat in ['Cerveza','Licor']:
        g=[p for p in ps if p['category']==cat]
        if g: st.subheader(cat)
        for p in g:
            op,op_bottles=session_qty_detail(d.isoformat(),p['id'],'OPENING',bar)
            if op is not None: default,default_bottles=op,op_bottles
            else:
                lc,lc_bottles,_=last_close_detail(p['id'],bar,d.isoformat()); default,default_bottles=(lc or 0),lc_bottles
            with st.expander(product_label(p),expanded=True):
                if op is not None:
                    if cat=='Licor' and not p['bottle_ml'] and op_bottles is not None: st.caption(f"Apertura de hoy: **{op_bottles:.2f} botellas** · ml pendiente")
                    else: st.caption(f"Apertura de hoy: **{qty_fmt(p,op)}**")
                else:
                    st.caption("No se encontró apertura de hoy para este producto; se usa el último cierre disponible como valor inicial sugerido.")
                res=bottle_count_input(p,f"cl_{cycle}_{d}_{p['id']}",default,default_bottles); val=res['base']
                counts.append({'pid':p['id'],'lid':bar,'qty':val,'bottle_equiv':res['bottles']})
    st.info(f"Productos a contar: {len(ps)} · Tipo: {cycle_label}")
    st.divider(); pending=[]
    st.subheader("Movimientos pendientes del día")
    st.caption("Solo registra aquí lo que todavía NO haya sido ingresado desde las opciones independientes. Puedes seleccionar cualquier cerveza o licor, aunque no forme parte del conteo diario.")
    if st.toggle("¿Hoy se recibieron productos de proveedor que aún no han sido registrados?"):
        n=int(st.number_input("Número de productos recibidos",1,30,1,key='cl_sup_n')); supplier=st.text_input("Proveedor (opcional)",key='cl_sup_name'); ref=st.text_input("Factura / referencia (opcional)",key='cl_sup_ref')
        mp={product_label(p):p for p in all_ps}
        for i in range(n):
            nm=st.selectbox(f"Producto recibido {i+1}",list(mp),key=f'cl_sup_p{i}'); p=mp[nm]; mv=movement_qty_input(p,f'cl_sup_q{i}')
            if mv['base']>0 or (mv['bottles'] or 0)>0: pending.append(('SUPPLIER',p['id'],mv['base'],mv['bottles'],None,wh,supplier,ref,''))
    if st.toggle("¿Hoy se trasladaron productos de bodega al bar que aún no han sido registrados?"):
        n=int(st.number_input("Número de productos trasladados",1,30,1,key='cl_tr_n')); mp={product_label(p):p for p in all_ps}
        for i in range(n):
            nm=st.selectbox(f"Producto trasladado {i+1}",list(mp),key=f'cl_tr_p{i}'); p=mp[nm]; mv=movement_qty_input(p,f'cl_tr_q{i}')
            if mv['base']>0 or (mv['bottles'] or 0)>0: pending.append(('TRANSFER',p['id'],mv['base'],mv['bottles'],wh,bar,None,None,''))
    if st.toggle("¿Hoy se realizaron pruebas, hubo desperdicios o se dieron cortesías?"):
        n=int(st.number_input("¿Cuántos registros necesitas ingresar?",1,30,1,key='cl_adj_n')); mp={product_label(p):p for p in all_ps}
        for i in range(n):
            c1,c2=st.columns([1,2]); typ=c1.selectbox(f"Tipo {i+1}",['Prueba','Desperdicio','Cortesía'],key=f'cl_adj_t{i}'); nm=c2.selectbox(f"Producto {i+1}",list(mp),key=f'cl_adj_p{i}'); p=mp[nm]
            mv=movement_qty_input(p,f'cl_adj_q{i}'); obs=st.text_input(f"Observación {i+1} (opcional)",key=f'cl_adj_o{i}')
            typdb={'Prueba':'PRUEBA','Desperdicio':'DESPERDICIO','Cortesía':'CORTESIA'}[typ]
            if mv['base']>0 or (mv['bottles'] or 0)>0: pending.append((typdb,p['id'],mv['base'],mv['bottles'],bar,None,None,None,obs))
    notes=st.text_area("Observaciones generales (opcional)")
    if st.button("Guardar cierre",type="primary",width="stretch"):
        save_session('CLOSING',counts,d,notes,inventory_cycle=cycle)
        for typ,pid,qty,beq,fr,to,sup,ref,obs in pending:
            create_movement(typ,pid,qty,fr,to,sup,ref,obs,d,bottle_equiv=beq)
        st.success(f"Cierre {cycle_label.lower()} y movimientos pendientes guardados correctamente.")

elif page=='Recibir pedido':
    page_header("Recibir pedido", "Registra entradas de proveedor en bodega o bar.")
    st.caption("Opción adicional: úsala si puedes registrar el pedido cuando llega. Si no, podrá ingresarse más tarde desde apertura/cierre.")
    d=st.date_input("Fecha de recepción",value=date.today()); supplier=st.text_input("Proveedor"); ref=st.text_input("Factura / referencia (opcional)")
    wh=one("SELECT id FROM locations WHERE name='Bodega'")['id']; bar=one("SELECT id FROM locations WHERE name='Bar'")['id']
    dest_name=st.selectbox("Destino",['Bodega','Bar'],index=0,disabled=user['role']=='STAFF')
    dest=wh if dest_name=='Bodega' else bar
    ps=[p for p in products() if p['category'] in ('Cerveza','Licor')]; n=int(st.number_input("Número de productos recibidos",1,50,1)); mp={product_label(p):p for p in ps}; rows=[]
    for i in range(n):
        nm=st.selectbox(f"Producto {i+1}",list(mp),key=f'rp{i}'); p=mp[nm]; mv=movement_qty_input(p,f'rq{i}')
        obs=st.text_input(f"Observación {i+1} (opcional)",key=f'ro{i}')
        if mv['base']>0 or (mv['bottles'] or 0)>0: rows.append((p['id'],mv['base'],mv['bottles'],obs))
    if st.button("Confirmar recepción",type="primary",width="stretch"):
        if not rows: st.error("Ingresa al menos una cantidad mayor que cero.")
        else:
            for pid,qty,beq,obs in rows: create_movement('SUPPLIER',pid,qty,None,dest,supplier,ref,obs,d,bottle_equiv=beq)
            st.success(f"Recepción registrada en {dest_name}.")

elif page=='Trasladar productos':
    page_header("Trasladar productos", "Registra movimientos de inventario entre bodega y bar.")
    st.caption("Opción adicional para registrar un traslado en el momento. Si no hay tiempo, puede registrarse después como movimiento pendiente.")
    d=st.date_input("Fecha del traslado",value=date.today()); wh=one("SELECT id FROM locations WHERE name='Bodega'")['id']; bar=one("SELECT id FROM locations WHERE name='Bar'")['id']
    ps=[p for p in products() if p['category'] in ('Cerveza','Licor')]; n=int(st.number_input("Número de productos trasladados",1,50,1)); mp={product_label(p):p for p in ps}; rows=[]
    for i in range(n):
        nm=st.selectbox(f"Producto {i+1}",list(mp),key=f'tp{i}'); p=mp[nm]; mv=movement_qty_input(p,f'tq{i}')
        if mv['base']>0 or (mv['bottles'] or 0)>0: rows.append((p['id'],mv['base'],mv['bottles']))
    if st.button("Confirmar traslado Bodega → Bar",type="primary",width="stretch"):
        if not rows: st.error("Ingresa al menos una cantidad mayor que cero.")
        else:
            for pid,qty,beq in rows: create_movement('TRANSFER',pid,qty,wh,bar,d=d,bottle_equiv=beq)
            st.success("Traslado registrado.")

elif page=='POS / Ventas':
    page_header("POS / Ventas", "Registra ventas de cócteles, shots, cervezas y botellas para calcular el consumo teórico.")
    st.caption("Ingresa los totales vendidos del POS por fecha. Shots y cervezas quedan registrados directamente contra el producto correspondiente.")
    d=st.date_input("Fecha de ventas",value=date.today(),key='pos_date')
    tab_cocktail,tab_shot,tab_beer,tab_bottle=st.tabs(['🍹 Cócteles','🥃 Shots','🍺 Cervezas','🍾 Botellas de licor'])

    with tab_cocktail:
        items=q("SELECT * FROM cocktails WHERE active=1 ORDER BY name")
        if not items:
            st.info("No hay cócteles activos. Puedes crearlos en Administración → Cócteles / Recetas.")
        else:
            mp={r['name']:r['id'] for r in items}
            n=int(st.number_input("Número de cócteles con ventas",1,30,1,key='pos_c_n'))
            rows=[]
            for i in range(n):
                c1,c2=st.columns([2,1])
                nm=c1.selectbox(f"Cóctel {i+1}",list(mp),key=f'pos_c_name_{i}')
                qty=float(c2.number_input(f"Cantidad {i+1}",min_value=0,step=1,value=0,key=f'pos_c_qty_{i}'))
                if qty>0: rows.append((mp[nm],qty))
            obs=st.text_input("Observación general (opcional)",key='pos_c_obs')
            if st.button("Guardar ventas de cócteles",type='primary',width='stretch',key='save_pos_cocktails'):
                if not rows: st.error("Ingresa al menos una cantidad mayor que cero.")
                else:
                    for cid,qty in rows:
                        con.execute("INSERT INTO pos_sales(sale_date,cocktail_id,product_id,sale_type,quantity,oz_per_unit,user_id,observation,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                                    (d.isoformat(),cid,None,'Cóctel',qty,None,user['id'],obs,now_iso()))
                    con.commit(); backup_db_to_drive(); st.success(f"Ventas de cócteles guardadas: {len(rows)} registro(s).")

    with tab_shot:
        liquors=products('Licor')
        if not liquors:
            st.info("No hay licores activos.")
        else:
            mp={product_label(r):r for r in liquors}
            n=int(st.number_input("Número de licores vendidos como shot",1,30,1,key='pos_s_n'))
            rows=[]
            for i in range(n):
                c1,c2,c3=st.columns([2,1,1])
                nm=c1.selectbox(f"Licor {i+1}",list(mp),key=f'pos_s_name_{i}'); prod=mp[nm]
                qty=float(c2.number_input(f"Shots {i+1}",min_value=0,step=1,value=0,key=f'pos_s_qty_{i}'))
                oz=float(c3.number_input(f"Oz/shot {i+1}",min_value=.25,step=.25,value=1.0,key=f'pos_s_oz_{i}'))
                if qty>0: rows.append((prod['id'],qty,oz))
            obs=st.text_input("Observación general (opcional)",key='pos_s_obs')
            if st.button("Guardar ventas de shots",type='primary',width='stretch',key='save_pos_shots'):
                if not rows: st.error("Ingresa al menos una cantidad mayor que cero.")
                else:
                    for pid,qty,oz in rows:
                        con.execute("INSERT INTO pos_sales(sale_date,cocktail_id,product_id,sale_type,quantity,oz_per_unit,user_id,observation,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                                    (d.isoformat(),None,pid,'Shot',qty,oz,user['id'],obs,now_iso()))
                    con.commit(); backup_db_to_drive(); st.success(f"Ventas de shots guardadas: {len(rows)} registro(s).")

    with tab_beer:
        beers=products('Cerveza')
        if not beers:
            st.info("No hay cervezas activas.")
        else:
            st.caption("Escribe únicamente las unidades vendidas. Las cervezas en cero no generan registros.")
            beer_rows=[]
            cols=st.columns(2)
            for i,p in enumerate(beers):
                with cols[i%2]:
                    qty=float(st.number_input(product_label(p),min_value=0,step=1,value=0,key=f'pos_b_qty_{p["id"]}'))
                    if qty>0: beer_rows.append((p['id'],qty))
            obs=st.text_input("Observación general (opcional)",key='pos_b_obs')
            if st.button("Guardar ventas de cervezas",type='primary',width='stretch',key='save_pos_beers'):
                if not beer_rows: st.error("Ingresa al menos una cantidad mayor que cero.")
                else:
                    for pid,qty in beer_rows:
                        con.execute("INSERT INTO pos_sales(sale_date,cocktail_id,product_id,sale_type,quantity,oz_per_unit,user_id,observation,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                                    (d.isoformat(),None,pid,'Cerveza',qty,None,user['id'],obs,now_iso()))
                    con.commit(); backup_db_to_drive(); st.success(f"Ventas de cerveza guardadas: {len(beer_rows)} producto(s).")

    with tab_bottle:
        liquors=products('Licor')
        if not liquors:
            st.info("No hay licores activos.")
        else:
            mp={product_label(r):r for r in liquors}
            n=int(st.number_input("Número de licores vendidos por botella",1,20,1,key='pos_l_n'))
            rows=[]
            for i in range(n):
                c1,c2=st.columns([2,1])
                nm=c1.selectbox(f"Licor {i+1}",list(mp),key=f'pos_l_name_{i}'); prod=mp[nm]
                qty=float(c2.number_input(f"Botellas {i+1}",min_value=0,step=1,value=0,key=f'pos_l_qty_{i}'))
                if qty>0: rows.append((prod['id'],qty))
            obs=st.text_input("Observación general (opcional)",key='pos_l_obs')
            if st.button("Guardar ventas por botella",type='primary',width='stretch',key='save_pos_bottles'):
                if not rows: st.error("Ingresa al menos una cantidad mayor que cero.")
                else:
                    for pid,qty in rows:
                        con.execute("INSERT INTO pos_sales(sale_date,cocktail_id,product_id,sale_type,quantity,oz_per_unit,user_id,observation,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                                    (d.isoformat(),None,pid,'Botella de licor',qty,None,user['id'],obs,now_iso()))
                    con.commit(); backup_db_to_drive(); st.success(f"Ventas por botella guardadas: {len(rows)} registro(s).")

elif page=='Dashboard':
    page_header("Dashboard Gerencial", "Resumen ejecutivo del inventario, consumo, diferencias y abastecimiento.")
    period=st.selectbox("Periodo",['Hoy','7 días','14 días','28 días','Personalizado'],index=1)
    if period=='Hoy': d1=d2=date.today()
    elif period=='7 días': d2=date.today(); d1=d2-timedelta(days=6)
    elif period=='14 días': d2=date.today(); d1=d2-timedelta(days=13)
    elif period=='28 días': d2=date.today(); d1=d2-timedelta(days=27)
    else:
        a,b=st.columns(2); d1=a.date_input("Desde",value=date.today()-timedelta(days=6),key='dash1'); d2=b.date_input("Hasta",value=date.today(),key='dash2')
    if d2<d1: st.error("La fecha final no puede ser anterior a la inicial."); st.stop()

    data=consolidated(d1,d2)
    with_data=[r for r in data if r['Días completos']>0 or r['Consumo esperado']>0 or r['Ajustes']>0 or r['Alertas apertura']>0]
    alerts=[r for r in with_data if r['Estado']!='✅ OK']; ok=[r for r in with_data if r['Estado']=='✅ OK']
    liq_oz=sum(max(float(r['Consumo real'] or 0),0) for r in with_data if r['Categoría']=='Licor')
    beer_units=sum(max(float(r['Consumo real'] or 0),0) for r in with_data if r['Categoría']=='Cerveza')
    accuracies=[product_accuracy(r) for r in with_data]; accuracies=[x for x in accuracies if x is not None]
    accuracy=sum(accuracies)/len(accuracies) if accuracies else None
    known_costs=[difference_cost(r) for r in with_data]; known_costs=[x for x in known_costs if x is not None]
    diff_cost=sum(known_costs) if known_costs else None

    bar=one("SELECT id FROM locations WHERE name='Bar'")['id']; wh=one("SELECT id FROM locations WHERE name='Bodega'")['id']
    coverage=[]
    days=max((d2-d1).days+1,1)
    for r in with_data:
        daily=max(float(r['Consumo real'] or 0),0)/max(r['Días completos'],1) if r['Días completos'] else 0
        if daily>0:
            stock=max(current_stock(r['_pid'],bar)+current_stock(r['_pid'],wh),0)
            coverage.append((stock/daily,r['Producto']))
    critical=min(coverage,key=lambda x:x[0],default=None)

    k1,k2,k3=st.columns(3)
    k1.metric("Consumo del periodo",f"{liq_oz:,.1f} oz licor",delta=f"{beer_units:,.0f} cervezas/unid")
    k2.metric("Exactitud promedio",f"{accuracy:.1f}%" if accuracy is not None else "—")
    k3.metric("Productos con alerta",len(alerts),delta=f"{len(ok)} sin alerta")
    k4,k5,k6=st.columns(3)
    worst=max(with_data,key=lambda r:abs(r['Diferencia no explicada']),default=None)
    k4.metric("Mayor diferencia",f"{abs(worst['Diferencia no explicada']):.2f} {worst['_unit']}" if worst else "—",delta=worst['Producto'] if worst else None)
    k5.metric("Costo estimado diferencias",f"${diff_cost:,.2f}" if diff_cost is not None else "Pendiente costos")
    k6.metric("Cobertura crítica",f"{critical[0]:.1f} días" if critical else "—",delta=critical[1] if critical else None)

    st.caption("Exactitud = cercanía entre consumo físico y consumo explicado por POS/recetas/ajustes. El costo de diferencias aparece cuando se registre el costo por botella/unidad.")

    st.markdown('<div class="ramona-section">🚨 Alertas importantes</div>', unsafe_allow_html=True)
    if alerts:
        for r in sorted(alerts,key=lambda x:(-abs(x['Diferencia no explicada']),-x['Alertas apertura']))[:8]:
            unit=r['_unit']; diff=r['Diferencia no explicada']
            st.warning(f"{r['Producto']} · diferencia no explicada {diff:+.2f} {unit} · alertas apertura: {r['Alertas apertura']}")
    else:
        st.success("No hay alertas de inventario para el periodo seleccionado.")

    st.markdown('<div class="ramona-section">📦 Resumen por producto</div>', unsafe_allow_html=True)
    show=[]
    for r in with_data:
        p=r['_p']
        show.append({
            'Producto':r['Producto'], 'Categoría':r['Categoría'],
            'Consumo real':oz_and_bottles_text(p,r['Consumo real']),
            'Consumo esperado':oz_and_bottles_text(p,r['Consumo esperado']),
            'Diferencia':oz_and_bottles_text(p,abs(r['Diferencia no explicada'])),
            'Aperturas con alerta':r['Alertas apertura'],'Estado':r['Estado']})
    if show: st.dataframe(pd.DataFrame(show),width="stretch",hide_index=True)
    else: st.info("No hay días completos de apertura+cierre ni ventas/ajustes en este rango.")

    c1,c2=st.columns(2)
    with c1:
        st.subheader("🔥 Top consumo")
        top=sorted(with_data,key=lambda r:max(float(r['Consumo real'] or 0),0),reverse=True)[:5]
        if top:
            st.dataframe(pd.DataFrame([{'Producto':r['Producto'],'Consumo':oz_and_bottles_text(r['_p'],r['Consumo real'])} for r in top]),width="stretch",hide_index=True)
    with c2:
        st.subheader("⚠️ Top diferencias")
        topd=sorted(with_data,key=lambda r:abs(float(r['Diferencia no explicada'] or 0)),reverse=True)[:5]
        if topd:
            st.dataframe(pd.DataFrame([{'Producto':r['Producto'],'Diferencia':f"{r['Diferencia no explicada']:+.2f} {r['_unit']}",'Estado':r['Estado']} for r in topd]),width="stretch",hide_index=True)

    st.markdown('<div class="ramona-section">📈 Tendencia: consumo real vs esperado</div>', unsafe_allow_html=True)
    t1,t2=st.tabs(["Licores (oz)","Cervezas (unidades)"])
    with t1:
        t=daily_trend(d1,d2,'Licor')
        if len(t): st.line_chart(t.set_index('Fecha'),width="stretch")
        else: st.info("Sin datos suficientes de licores para graficar.")
    with t2:
        t=daily_trend(d1,d2,'Cerveza')
        if len(t): st.line_chart(t.set_index('Fecha'),width="stretch")
        else: st.info("Sin datos suficientes de cerveza para graficar.")

    st.divider(); st.markdown('<div class="ramona-section">Detalle para auditoría</div>', unsafe_allow_html=True)
    mode=st.selectbox("Mostrar",['Solo alertas de apertura','Aperturas','Cierres','Ambos'])
    if mode=='Solo alertas de apertura':
        df=pd.read_sql_query("""SELECT s.session_date Fecha,p.name Producto,ROUND(ic.previous_qty,2) 'Cierre anterior',ROUND(ic.qty_base,2) Apertura,ROUND(ic.variance,2) Diferencia,COALESCE(ic.observation,'') Observación,u.name Empleado
                              FROM inventory_counts ic JOIN inventory_sessions s ON s.id=ic.session_id JOIN products p ON p.id=ic.product_id JOIN users u ON u.id=s.user_id
                              WHERE s.session_type='OPENING' AND s.session_date BETWEEN ? AND ? AND ABS(COALESCE(ic.variance,0))>0 ORDER BY s.session_date DESC,p.name""",con,params=(d1.isoformat(),d2.isoformat()))
    else:
        types={'Aperturas':['OPENING'],'Cierres':['CLOSING'],'Ambos':['OPENING','CLOSING']}[mode]; placeholders=','.join('?'*len(types))
        df=pd.read_sql_query(f"""SELECT s.session_date Fecha,s.session_type Tipo,p.name Producto,ROUND(ic.qty_base,2) Conteo,COALESCE(ic.observation,'') Observación,u.name Empleado
                              FROM inventory_counts ic JOIN inventory_sessions s ON s.id=ic.session_id JOIN products p ON p.id=ic.product_id JOIN users u ON u.id=s.user_id
                              WHERE s.session_date BETWEEN ? AND ? AND s.session_type IN ({placeholders}) ORDER BY s.session_date DESC,s.session_type,p.name""",con,params=(d1.isoformat(),d2.isoformat(),*types))
    st.dataframe(df,width="stretch",hide_index=True)

elif page=='Abastecimiento':
    page_header("Abastecimiento", "Consumo en oz y botellas equivalentes para convertir inventario operativo en compras.")
    st.caption("Consumo en oz para operación y su equivalente en botellas para compras. La recomendación usa consumo real reciente + stock de seguridad − stock disponible.")
    lookback=int(st.selectbox("Histórico para estimar consumo",[14,21,28,42,56],index=2,format_func=lambda x:f"Últimos {x} días")); safety=float(setting('safety_stock_pct','15'))/100
    d2=date.today(); d1=d2-timedelta(days=lookback-1); data=consolidated(d1,d2); bar=one("SELECT id FROM locations WHERE name='Bar'")['id']; wh=one("SELECT id FROM locations WHERE name='Bodega'")['id']
    rows=[]; products_to_buy=0; total_buy_units=0
    for r in data:
        p=r['_p']; complete=max(r['Días completos'],0)
        weekly=max((r['Consumo real']/complete*7) if complete else 0,0)
        target=weekly*(1+safety); sb=max(current_stock(p['id'],bar),0); sw=max(current_stock(p['id'],wh),0); stock=max(sb+sw,0); need=max(target-stock,0)
        if p['category']=='Licor':
            boz=bottle_oz(p)
            if boz:
                buy=math.ceil(need/boz) if need>0 else 0
                buy_text=f"{buy} botellas" if buy!=1 else "1 botella"
            else:
                buy=None; buy_text="⚠ Falta ml"
        else:
            buy=math.ceil(need) if need>0 else 0
            buy_text=f"{buy} unidades"
        if buy and buy>0: products_to_buy+=1; total_buy_units+=buy
        rows.append({
            'Producto':product_label(p),
            'Consumo semanal · oz / bot':oz_and_bottles_text(p,weekly),
            'Stock Bar · oz / bot':oz_and_bottles_text(p,sb),
            'Stock Bodega · oz / bot':oz_and_bottles_text(p,sw),
            'Stock total · oz / bot':oz_and_bottles_text(p,stock),
            'Seguridad':f"{int(safety*100)}%",'Comprar':buy_text,'Días usados':complete,'_buy':buy or 0,'_stock':stock})
    if rows:
        k1,k2,k3=st.columns(3)
        k1.metric("Productos por reponer",products_to_buy)
        k2.metric("Margen de seguridad",f"{int(safety*100)}%")
        missing=sum(1 for x in rows if x['Comprar']=='⚠ Falta ml')
        k3.metric("Licores sin presentación",missing)
        df=pd.DataFrame(rows).sort_values(['_buy','Producto'],ascending=[False,True])
        df=df[(df['Días usados']>0) | (df['_stock']>0)].drop(columns=['_buy','_stock'])
        st.dataframe(df,width="stretch",hide_index=True,column_config={'Días usados':st.column_config.NumberColumn(format='%d')})
    else: st.info("Aún no hay suficiente información para estimar abastecimiento.")
    st.caption("En licores sin presentación en ml no se genera una compra estimada: primero debe completarse la presentación para convertir oz a botellas con precisión.")

elif page=='Reporte PDF':
    page_header("Reportes", "Genera un reporte consolidado del período seleccionado.")
    a,b=st.columns(2); d1=a.date_input("Desde",value=date.today()-timedelta(days=6),key='pdf1'); d2=b.date_input("Hasta",value=date.today(),key='pdf2')
    if st.button("Generar reporte consolidado",type="primary"):
        data=[r for r in consolidated(d1,d2) if r['Días completos']>0 or r['Consumo esperado']>0 or r['Ajustes']>0 or r['Alertas apertura']>0]
        buf=io.BytesIO(); doc=SimpleDocTemplate(buf,pagesize=landscape(letter),leftMargin=24,rightMargin=24,topMargin=24,bottomMargin=24); sty=getSampleStyleSheet()
        story=[Paragraph("INVENTARIO LA RAMONA — REPORTE CONSOLIDADO",sty['Title']),Paragraph(f"Periodo: {d1} a {d2}",sty['Normal']),Spacer(1,10)]
        tbl=[["Producto","Cat.","Inicial","Final","Entradas","Real","Esperado","Ajustes","Diferencia","Alertas","Estado"]]
        for r in data: tbl.append([r['Producto'],r['Categoría'],f"{r['Inicial']:.2f}" if r['Inicial'] is not None else '—',f"{r['Final']:.2f}" if r['Final'] is not None else '—',f"{r['Entradas al bar']:.2f}",f"{r['Consumo real']:.2f}",f"{r['Consumo esperado']:.2f}",f"{r['Ajustes']:.2f}",f"{r['Diferencia no explicada']:+.2f}",r['Alertas apertura'],r['Estado'].replace('✅','').replace('⚠️','').replace('🔴','')])
        t=Table(tbl,repeatRows=1,colWidths=[125,45,48,48,48,48,55,48,58,42,55]); t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E8E8E8')),('GRID',(0,0),(-1,-1),.25,colors.grey),('FONTSIZE',(0,0),(-1,-1),7),('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
        story.append(t); doc.build(story); buf.seek(0)
        st.download_button("Descargar PDF",buf,file_name=f"inventario_la_ramona_{d1}_{d2}.pdf",mime="application/pdf")

elif page=='Administración':
    page_header("Configuración y administración", "Productos, recetas, usuarios, importaciones y parámetros del sistema.")
    t1,t2,t3,t4,t5=st.tabs(['Productos','Cócteles / Recetas','Usuarios','Importar Excel','Configuración'])
    with t1:
        st.subheader("Agregar / actualizar producto")
        cats=q("SELECT * FROM categories WHERE name IN ('Cerveza','Licor') ORDER BY name"); cm={r['name']:r['id'] for r in cats}; cat=st.selectbox("Categoría",list(cm)); name=st.text_input("Nombre del producto"); ml=st.number_input("Presentación (ml)",min_value=0.0,value=0.0,step=5.0); pkg=st.selectbox("Envase",['Botella','Lata','Otro'])
        principal_new=st.checkbox("Incluir este licor en el inventario diario",value=False,disabled=(cat!='Licor'),key='new_daily_liquor')
        if st.button("Agregar producto",type="primary") and name.strip():
            try:
                ex("INSERT INTO products(category_id,name,bottle_ml,package_type,daily_inventory) VALUES(?,?,?,?,?)",(cm[cat],name.strip(),ml or None,pkg,1 if (cat=='Licor' and principal_new) else 0)); st.success("Producto agregado."); st.rerun()
            except sqlite3.IntegrityError: st.error("Ese producto con la misma presentación ya existe.")
        st.caption("La presentación en ml puede completarse más adelante. Mientras esté pendiente, el inventario de licor se guarda como botellas completas + fracción; al registrar los ml, la app convierte automáticamente esos conteos a oz. El costo es opcional.")
        df=pd.read_sql_query("SELECT p.id ID,c.name Categoría,p.name Producto,p.bottle_ml 'ml',p.package_type Envase,p.unit_cost 'Costo por botella/unidad',CASE WHEN c.name='Cerveza' THEN 'Diario' WHEN p.daily_inventory=1 THEN 'Principal · Diario' ELSE 'Semanal' END 'Frecuencia inventario',p.active Activo FROM products p JOIN categories c ON c.id=p.category_id ORDER BY c.name,p.name",con)
        st.dataframe(df,width="stretch",hide_index=True)
        st.markdown("#### Licores principales del inventario diario")
        st.caption("Las cervezas siempre son diarias. Selecciona aquí qué licores deben aparecer también en el inventario diario; los demás aparecerán únicamente cuando selecciones inventario semanal.")
        liquor_rows=products('Licor')
        liquor_map={product_label(r):r for r in liquor_rows}
        selected_default=[label for label,r in liquor_map.items() if int(r['daily_inventory'] or 0)==1]
        selected_daily=st.multiselect("Licores principales",list(liquor_map.keys()),default=selected_default,key='daily_liquors_multiselect')
        if st.button("Guardar licores principales",width="stretch"):
            con.execute("UPDATE products SET daily_inventory=0 WHERE category_id=(SELECT id FROM categories WHERE name='Licor')")
            for label in selected_daily:
                con.execute("UPDATE products SET daily_inventory=1 WHERE id=?",(liquor_map[label]['id'],))
            con.commit(); backup_db_to_drive(); st.success("Lista de licores principales actualizada."); st.rerun()
        pid=st.number_input("ID del producto a actualizar",min_value=1,step=1); newml=st.number_input("Nuevo ml",min_value=0.0,step=5.0,key='updml'); newcost=st.number_input("Costo por botella/unidad ($, opcional)",min_value=0.0,step=.01,key='updcost')
        if st.button("Actualizar presentación / costo"):
            ex("UPDATE products SET bottle_ml=?,unit_cost=? WHERE id=?",(newml or None,newcost or None,int(pid)))
            if newml>0: backfill_product_bottle_counts(int(pid))
            st.success("Producto actualizado. Si había conteos guardados por botellas, sus oz fueron recalculadas automáticamente."); st.rerun()
    with t2:
        cn=st.text_input("Nombre del cóctel")
        if st.button("Crear cóctel") and cn.strip():
            try: ex("INSERT INTO cocktails(name) VALUES(?)",(cn.strip(),)); st.success("Cóctel creado."); st.rerun()
            except sqlite3.IntegrityError: st.error("Ya existe.")
        cs=q("SELECT * FROM cocktails WHERE active=1 ORDER BY name"); ls=products('Licor')
        if cs and ls:
            cmap={r['name']:r['id'] for r in cs}; lmap={product_label(r):r['id'] for r in ls}; c=st.selectbox("Cóctel",list(cmap),key='rc'); l=st.selectbox("Licor",list(lmap),key='rl'); oz=st.number_input("Oz por cóctel",min_value=.25,step=.25,value=1.0)
            if st.button("Agregar / actualizar ingrediente"):
                con.execute("INSERT INTO recipes(cocktail_id,product_id,oz_qty) VALUES(?,?,?) ON CONFLICT(cocktail_id,product_id) DO UPDATE SET oz_qty=excluded.oz_qty",(cmap[c],lmap[l],oz)); con.commit(); st.success("Receta actualizada.")
        st.dataframe(pd.read_sql_query("SELECT c.name Cóctel,p.name Licor,r.oz_qty 'Oz por cóctel' FROM recipes r JOIN cocktails c ON c.id=r.cocktail_id JOIN products p ON p.id=r.product_id ORDER BY c.name,p.name",con),width="stretch",hide_index=True)
    with t3:
        st.subheader("Usuarios autorizados")
        st.caption("Solo los correos de esta lista con estado Activo pueden entrar con Google. Compartir el enlace no da acceso.")
        email=st.text_input("Correo Google / Gmail").strip().lower()
        un=st.text_input("Nombre del usuario")
        owner_email=normalized_email(secret_value('app','bootstrap_admin_email'))
        is_owner=normalized_email(user['email'])==owner_email
        assignable_roles=['STAFF','MANAGER','GENERAL_MANAGER','ADMIN'] if is_owner else ['STAFF','MANAGER','GENERAL_MANAGER']
        role=st.selectbox("Rol",assignable_roles,format_func=lambda x:ROLE_LABELS.get(x,x))
        st.caption("MANAGER GENERAL puede administrar productos, recetas y usuarios. Solo la cuenta Developer/Owner configurada puede otorgar o modificar el rol ADMIN.")
        if st.button("Autorizar usuario",type="primary",width="stretch"):
            if not email or '@' not in email:
                st.error("Ingresa un correo válido.")
            else:
                existing=one("SELECT * FROM users WHERE lower(email)=?",(email,))
                if existing and existing['role']=='ADMIN' and not is_owner:
                    st.error("Solo la cuenta Developer/Owner puede modificar un usuario ADMIN.")
                elif existing:
                    ex("UPDATE users SET name=?,role=?,active=1 WHERE id=?",(un.strip() or existing['name'],role,existing['id']))
                    st.success("Usuario actualizado y activado."); st.rerun()
                else:
                    base_name=un.strip() or email.split('@')[0]
                    candidate=base_name; i=2
                    while one("SELECT 1 FROM users WHERE name=?",(candidate,)):
                        candidate=f"{base_name} {i}"; i+=1
                    ex("INSERT INTO users(name,pin_hash,email,role,active,created_at) VALUES(?,?,?,?,1,?)",(candidate,'',email,role,now_iso()))
                    st.success("Correo autorizado. Ya puede entrar con Google."); st.rerun()
        users_df=pd.read_sql_query("SELECT id ID,name Nombre,email Email,CASE role WHEN 'GENERAL_MANAGER' THEN 'MANAGER GENERAL' ELSE role END Rol,CASE active WHEN 1 THEN 'Activo' ELSE 'Bloqueado' END Estado,last_login_at 'Último acceso' FROM users WHERE email IS NOT NULL AND email<>'' ORDER BY active DESC,role,name",con)
        st.dataframe(users_df,width="stretch",hide_index=True)
        if is_owner:
            manageable=q("SELECT id,name,email,role,active FROM users WHERE email IS NOT NULL AND email<>'' ORDER BY name")
        else:
            manageable=q("SELECT id,name,email,role,active FROM users WHERE email IS NOT NULL AND email<>'' AND role<>'ADMIN' ORDER BY name")
        if manageable:
            labels={f"{r['name']} · {r['email']} · {ROLE_LABELS.get(r['role'],r['role'])} · {'Activo' if r['active'] else 'Bloqueado'}":r for r in manageable}
            sel=st.selectbox("Gestionar usuario",list(labels.keys()))
            target=labels[sel]
            c1,c2=st.columns(2)
            if target['active']:
                if c1.button("Bloquear acceso",width="stretch"):
                    if target['id']==user['id']:
                        st.error("No puedes bloquear tu propia cuenta mientras estás conectado.")
                    else:
                        ex("UPDATE users SET active=0 WHERE id=?",(target['id'],)); st.success("Usuario bloqueado."); st.rerun()
            else:
                if c1.button("Reactivar acceso",width="stretch"):
                    ex("UPDATE users SET active=1 WHERE id=?",(target['id'],)); st.success("Usuario reactivado."); st.rerun()
            role_options=['STAFF','MANAGER','GENERAL_MANAGER','ADMIN'] if is_owner else ['STAFF','MANAGER','GENERAL_MANAGER']
            current_role=target['role'] if target['role'] in role_options else role_options[0]
            new_role=c2.selectbox("Cambiar rol",role_options,index=role_options.index(current_role),format_func=lambda x:ROLE_LABELS.get(x,x),key='manage_role')
            if c2.button("Guardar rol",width="stretch"):
                if target['id']==user['id'] and new_role!=target['role']:
                    st.warning("Estás cambiando tu propio rol. El cambio se aplicará inmediatamente al recargar.")
                ex("UPDATE users SET role=? WHERE id=?",(new_role,target['id'])); st.success("Rol actualizado."); st.rerun()
    with t4:
        st.subheader("Importar catálogo / recetas / ventas desde Excel")
        st.caption("Carga una exportación .xlsx del Google Sheet. Se importa solo información estructurada; los registros ambiguos se dejan para revisión y no se inventan datos.")
        up=st.file_uploader("Archivo Excel",type=['xlsx'])
        if up:
            try:
                xls=pd.ExcelFile(up)
                st.write("Hojas detectadas:",", ".join(xls.sheet_names))
                if st.button("Importar datos reconocibles",type="primary"):
                    imported=0
                    if 'PRODUCTOS' in xls.sheet_names:
                        dfp=pd.read_excel(xls,'PRODUCTOS')
                        for _,r in dfp.dropna(subset=['Producto']).iterrows():
                            cat=str(r.get('Categoría','Licor')).strip() or 'Licor'; cid=one("SELECT id FROM categories WHERE name=?",(cat,));
                            if not cid: continue
                            mlv=pd.to_numeric(r.get('Tamaño botella (ml)'),errors='coerce'); mlv=None if pd.isna(mlv) else float(mlv)
                            try: con.execute("INSERT OR IGNORE INTO products(category_id,name,bottle_ml,package_type) VALUES(?,?,?,'Botella')",(cid['id'],str(r['Producto']).strip(),mlv)); imported+=1
                            except: pass
                    if 'RECETAS' in xls.sheet_names:
                        dfr=pd.read_excel(xls,'RECETAS')
                        for _,r in dfr.dropna(subset=['Cóctel','Licor']).iterrows():
                            cr=str(r['Cóctel']).strip(); lr=str(r['Licor']).strip(); oz=pd.to_numeric(r.get('Oz por cóctel'),errors='coerce')
                            if pd.isna(oz): continue
                            con.execute("INSERT OR IGNORE INTO cocktails(name) VALUES(?)",(cr,)); c=one("SELECT id FROM cocktails WHERE name=?",(cr,)); p=one("SELECT id FROM products WHERE lower(name)=lower(?) ORDER BY id LIMIT 1",(lr,))
                            if c and p: con.execute("INSERT INTO recipes(cocktail_id,product_id,oz_qty) VALUES(?,?,?) ON CONFLICT(cocktail_id,product_id) DO UPDATE SET oz_qty=excluded.oz_qty",(c['id'],p['id'],float(oz))); imported+=1
                    con.commit(); st.success(f"Importación terminada. Registros procesados: {imported}"); st.rerun()
            except Exception as e: st.error(f"No se pudo leer el archivo: {e}")
    with t5:
        st.subheader("Respaldo automático")
        cfg=_gdrive_cfg()
        if cfg['enabled'] and cfg['folder_id'] and cfg['service_account_json']:
            last=st.session_state.get('_last_drive_backup','Aún no realizado en esta sesión')
            st.success(f"Google Drive configurado · último respaldo: {last}")
            if st.button("Respaldar ahora en Google Drive",width="stretch"):
                ok,msg=backup_db_to_drive(force=True); (st.success if ok else st.error)(msg)
        else:
            st.warning("Respaldo Drive aún no configurado. La app funciona, pero la base local de Streamlit no debe considerarse almacenamiento permanente.")
        if os.path.exists(DB):
            with open(DB,'rb') as fh:
                st.download_button("Descargar copia de la base SQLite",data=fh.read(),file_name=f"bar_inventory_backup_{date.today().isoformat()}.db",mime="application/octet-stream",width="stretch")
        st.divider()
        if user['role']=='ADMIN':
            st.subheader("Inicio de operación / limpiar datos históricos")
            st.caption("Solo ADMIN puede ejecutar este reinicio. La herramienta elimina datos transaccionales anteriores: inventarios, POS/ventas y movimientos. Conserva productos, categorías, presentaciones, recetas, usuarios, roles y configuración.")
            inv_sessions=one("SELECT COUNT(*) n FROM inventory_sessions")['n']
            inv_counts=one("SELECT COUNT(*) n FROM inventory_counts")['n']
            pos_rows=one("SELECT COUNT(*) n FROM pos_sales")['n']
            mov_rows=one("SELECT COUNT(*) n FROM movements")['n']
            st.info(f"Datos actuales: {inv_sessions} sesiones · {inv_counts} conteos · {pos_rows} registros POS/ventas · {mov_rows} movimientos.")
            confirm_reset=st.text_input("Para confirmar escribe exactamente: INICIAR DESDE CERO",key="reset_inventory_confirm")
            if st.button("Dejar operación en cero",type="secondary",width="stretch"):
                if confirm_reset.strip() != "INICIAR DESDE CERO":
                    st.error("Confirmación incorrecta. Escribe exactamente: INICIAR DESDE CERO")
                else:
                    try:
                        con.execute("DELETE FROM inventory_counts")
                        con.execute("DELETE FROM inventory_sessions")
                        con.execute("DELETE FROM pos_sales")
                        con.execute("DELETE FROM movements")
                        con.execute("INSERT INTO settings(key,value) VALUES('sheet_history_seeded','1') ON CONFLICT(key) DO UPDATE SET value='1'")
                        con.execute("INSERT INTO settings(key,value) VALUES('production_inventory_started_at',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(now_iso(),))
                        con.commit()
                        backup_db_to_drive()
                        st.success("Operación reiniciada en cero. Se eliminaron inventarios, POS/ventas y movimientos anteriores. Productos, recetas, usuarios, roles y configuración permanecen intactos. El próximo conteo será la nueva línea base.")
                        st.rerun()
                    except Exception as e:
                        con.rollback()
                        st.error(f"No se pudo limpiar los datos históricos: {e}")
            st.divider()
        else:
            st.info("El reinicio total de datos operativos está reservado para el rol ADMIN.")
            st.divider()
        safety=st.number_input("Stock de seguridad para abastecimiento (%)",min_value=0,max_value=100,value=int(float(setting('safety_stock_pct','15'))),step=1)
        tb=st.number_input("Tolerancia cerveza (botellas)",min_value=0.0,value=float(setting('tolerance_beer','1')),step=.5)
        tl=st.number_input("Tolerancia licor (oz)",min_value=0.0,value=float(setting('tolerance_liquor','1')),step=.25)
        if st.button("Guardar configuración",type="primary"):
            for k,v in [('safety_stock_pct',safety),('tolerance_beer',tb),('tolerance_liquor',tl)]: con.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(k,str(v)))
            con.commit(); st.success("Configuración guardada.")
