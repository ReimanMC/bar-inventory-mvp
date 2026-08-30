import streamlit as st
import sqlite3, hashlib, io, math, re, unicodedata
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

st.set_page_config(page_title="Inventario La Ramona", page_icon="🍸", layout="wide")
st.markdown("""
<style>
.block-container{padding-top:1.2rem;padding-bottom:3rem;max-width:1250px}
div[data-testid="stMetric"]{border:1px solid rgba(128,128,128,.22);padding:10px;border-radius:10px}
.small-note{font-size:.86rem;opacity:.75}
@media (max-width: 700px){
  .block-container{padding-left:.65rem;padding-right:.65rem}
  div[data-testid="stHorizontalBlock"]{gap:.35rem}
}
</style>
""", unsafe_allow_html=True)

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
def ex(sql, p=()): con.execute(sql, p); con.commit()

def now_iso(): return datetime.now().isoformat(timespec="seconds")
def hash_pin(pin): return hashlib.sha256(pin.encode()).hexdigest()

def init_db():
    con.executescript("""
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, pin_hash TEXT NOT NULL DEFAULT '', email TEXT UNIQUE,
      role TEXT NOT NULL CHECK(role IN ('STAFF','MANAGER','ADMIN')), active INTEGER DEFAULT 1,
      last_login_at TEXT, created_at TEXT);
    CREATE TABLE IF NOT EXISTS categories(
      id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, count_unit TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS products(
      id INTEGER PRIMARY KEY, category_id INTEGER NOT NULL, name TEXT NOT NULL,
      bottle_ml REAL, package_type TEXT DEFAULT 'Botella', active INTEGER DEFAULT 1,
      UNIQUE(name,bottle_ml,package_type), FOREIGN KEY(category_id) REFERENCES categories(id));
    CREATE TABLE IF NOT EXISTS locations(id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);
    CREATE TABLE IF NOT EXISTS inventory_sessions(
      id INTEGER PRIMARY KEY, session_date TEXT NOT NULL, session_type TEXT NOT NULL,
      user_id INTEGER, created_at TEXT NOT NULL, submitted INTEGER DEFAULT 1, notes TEXT,
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

def save_session(kind, counts, session_date=None, notes=""):
    d=(session_date or date.today()).isoformat() if hasattr((session_date or date.today()),'isoformat') else str(session_date)
    cur=con.execute("INSERT INTO inventory_sessions(session_date,session_type,user_id,created_at,notes) VALUES(?,?,?,?,?)",
                    (d,kind,user['id'],now_iso(),notes)); sid=cur.lastrowid
    for x in counts:
        con.execute("""INSERT INTO inventory_counts(session_id,product_id,location_id,qty_base,previous_qty,variance,observation)
                       VALUES(?,?,?,?,?,?,?)""",(sid,x['pid'],x['lid'],x['qty'],x.get('prev'),x.get('var'),x.get('obs')))
    con.commit(); return sid

def count_input(p, key, default=0.0):
    default = max(float(default or 0),0)
    if p['category']=='Cerveza':
        return float(st.number_input("Conteo actual",min_value=0,value=int(round(default)),step=1,key=key))
    if not p['bottle_ml']:
        st.caption("Presentación en ml pendiente. Por ahora registra el total directamente en oz.")
        return float(st.number_input("Total actual (oz)",min_value=0.0,value=float(round(default,2)),step=.25,key=key))
    oz=float(p['bottle_ml'])/ML_PER_OZ; full=int(default//oz); rem=max(0.0,default-full*oz)
    a,b=st.columns(2)
    f=a.number_input("Botellas completas",min_value=0,value=full,step=1,key=key+'f')
    o=b.number_input("Botella abierta (oz)",min_value=0.0,max_value=float(round(oz,2)),value=float(min(round(rem,2),round(oz,2))),step=.25,key=key+'o')
    total=f*oz+o; st.caption(f"{p['bottle_ml']:.0f} ml = {oz:.2f} oz · Total: {total:.2f} oz")
    return total

def movement_qty_input(p,key,label="Cantidad"):
    step=1.0 if p['category']=='Cerveza' else .25
    return float(st.number_input(f"{label} ({unit_label(p)})",min_value=0.0,step=step,key=key))

def create_movement(typ,pid,qty,from_id=None,to_id=None,supplier=None,reference=None,obs="",d=None):
    con.execute("""INSERT INTO movements(movement_date,movement_type,product_id,qty_base,from_location_id,to_location_id,user_id,supplier,reference,observation,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?)""",((d or date.today()).isoformat(),typ,pid,qty,from_id,to_id,user['id'],supplier,reference,obs,now_iso()))
    con.commit()

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
    st.title("🍸 Inventario La Ramona")
    st.caption("Control de inventario · V0.3 · Acceso seguro con Google")
    st.write("Inicia sesión con la cuenta de Google autorizada por el administrador.")
    st.button("Continuar con Google",type="primary",use_container_width=True,on_click=st.login)
    st.caption("Tener el enlace de la aplicación no concede acceso. El correo debe estar autorizado y activo.")

if not st.user.is_logged_in:
    login_screen(); st.stop()

identity=google_identity()
bootstrap_admin(identity)
user_row=one("SELECT * FROM users WHERE lower(email)=?",(identity['email'],)) if identity else None
if not user_row or not user_row['active']:
    st.title("🔒 Acceso no autorizado")
    if identity:
        st.write(f"La cuenta **{identity['email']}** no tiene acceso activo a Inventario La Ramona.")
    st.caption("Solicita al administrador que autorice o reactive este correo.")
    st.button("Cerrar sesión",use_container_width=True,on_click=st.logout)
    st.stop()

user=dict(user_row)
ex("UPDATE users SET last_login_at=? WHERE id=?",(now_iso(),user['id']))

with st.sidebar:
    st.markdown(f"### {user['name']}")
    st.caption(f"{user['role']} · {user['email']}")
    pages=['Apertura','Cierre','Recibir pedido','Trasladar productos']
    if user['role'] in ('MANAGER','ADMIN'): pages += ['POS / Ventas','Dashboard','Abastecimiento','Reporte PDF']
    if user['role']=='ADMIN': pages += ['Administración']
    page=st.radio("Menú",pages)
    if st.button("Cerrar sesión",use_container_width=True): st.logout()

# --------------------------- pages ---------------------------
if page=='Apertura':
    st.title("Apertura")
    st.caption("Compara el conteo actual con el último cierre. Si no existe cierre anterior, el primer conteo se guarda como línea base y no genera alerta.")
    d=st.date_input("Fecha de apertura",value=date.today())
    bar=one("SELECT id FROM locations WHERE name='Bar'")['id']; ps=[p for p in products() if p['category'] in ('Cerveza','Licor')]
    counts=[]; missing_obs=False
    for cat in ['Cerveza','Licor']:
        g=[p for p in ps if p['category']==cat]
        if g: st.subheader(cat)
        for p in g:
            prev,prev_date=last_close(p['id'],bar,d.isoformat())
            with st.expander(product_label(p),expanded=True):
                if prev is None:
                    st.info("Primer inventario registrado para este producto. No existe cierre anterior para comparar.")
                    val=count_input(p,f"op_{d}_{p['id']}",0); var=None; obs=''
                else:
                    st.caption(f"Cierre anterior ({prev_date}): **{qty_fmt(p,prev)}**")
                    val=count_input(p,f"op_{d}_{p['id']}",prev); var=val-prev; obs=''
                    tol=float(setting('tolerance_beer','1')) if cat=='Cerveza' else float(setting('tolerance_liquor','1'))
                    if abs(var)>tol:
                        st.warning(f"Diferencia contra cierre anterior: {var:+.2f} {unit_label(p)}")
                        obs=st.text_input("Observación obligatoria",key=f"opobs_{d}_{p['id']}")
                        missing_obs |= not bool(obs.strip())
                    else: st.caption(f"Diferencia: {var:+.2f} {unit_label(p)} · dentro de tolerancia")
                counts.append({'pid':p['id'],'lid':bar,'qty':val,'prev':prev,'var':var,'obs':obs})
    if st.button("Guardar apertura",type="primary",use_container_width=True):
        if missing_obs: st.error("Falta explicar una diferencia marcada como alerta.")
        else: save_session('OPENING',counts,d); st.success("Apertura guardada correctamente.")

elif page=='Cierre':
    st.title("Cierre")
    d=st.date_input("Fecha de cierre",value=date.today())
    bar=one("SELECT id FROM locations WHERE name='Bar'")['id']; wh=one("SELECT id FROM locations WHERE name='Bodega'")['id']; ps=[p for p in products() if p['category'] in ('Cerveza','Licor')]
    counts=[]
    for cat in ['Cerveza','Licor']:
        g=[p for p in ps if p['category']==cat]
        if g: st.subheader(cat)
        for p in g:
            op=session_qty(d.isoformat(),p['id'],'OPENING',bar)
            default=op if op is not None else (last_close(p['id'],bar,d.isoformat())[0] or 0)
            with st.expander(product_label(p),expanded=True):
                if op is not None: st.caption(f"Apertura de hoy: **{qty_fmt(p,op)}**")
                val=count_input(p,f"cl_{d}_{p['id']}",default)
                counts.append({'pid':p['id'],'lid':bar,'qty':val})
    st.divider(); pending=[]
    st.subheader("Movimientos pendientes del día")
    st.caption("Solo registra aquí lo que todavía NO haya sido ingresado desde las opciones independientes.")
    if st.toggle("¿Hoy se recibieron productos de proveedor que aún no han sido registrados?"):
        n=int(st.number_input("Número de productos recibidos",1,30,1,key='cl_sup_n')); supplier=st.text_input("Proveedor (opcional)",key='cl_sup_name'); ref=st.text_input("Factura / referencia (opcional)",key='cl_sup_ref')
        mp={product_label(p):p for p in ps}
        for i in range(n):
            nm=st.selectbox(f"Producto recibido {i+1}",list(mp),key=f'cl_sup_p{i}'); p=mp[nm]; qty=movement_qty_input(p,f'cl_sup_q{i}')
            if qty>0: pending.append(('SUPPLIER',p['id'],qty,None,wh,supplier,ref,''))
    if st.toggle("¿Hoy se trasladaron productos de bodega al bar que aún no han sido registrados?"):
        n=int(st.number_input("Número de productos trasladados",1,30,1,key='cl_tr_n')); mp={product_label(p):p for p in ps}
        for i in range(n):
            nm=st.selectbox(f"Producto trasladado {i+1}",list(mp),key=f'cl_tr_p{i}'); p=mp[nm]; qty=movement_qty_input(p,f'cl_tr_q{i}')
            if qty>0: pending.append(('TRANSFER',p['id'],qty,wh,bar,None,None,''))
    if st.toggle("¿Hoy se realizaron pruebas, hubo desperdicios o se dieron cortesías?"):
        n=int(st.number_input("¿Cuántos registros necesitas ingresar?",1,30,1,key='cl_adj_n')); mp={product_label(p):p for p in ps}
        for i in range(n):
            c1,c2=st.columns([1,2]); typ=c1.selectbox(f"Tipo {i+1}",['Prueba','Desperdicio','Cortesía'],key=f'cl_adj_t{i}'); nm=c2.selectbox(f"Producto {i+1}",list(mp),key=f'cl_adj_p{i}'); p=mp[nm]
            qty=movement_qty_input(p,f'cl_adj_q{i}'); obs=st.text_input(f"Observación {i+1} (opcional)",key=f'cl_adj_o{i}')
            typdb={'Prueba':'PRUEBA','Desperdicio':'DESPERDICIO','Cortesía':'CORTESIA'}[typ]
            if qty>0: pending.append((typdb,p['id'],qty,bar,None,None,None,obs))
    notes=st.text_area("Observaciones generales (opcional)")
    if st.button("Guardar cierre",type="primary",use_container_width=True):
        save_session('CLOSING',counts,d,notes)
        for typ,pid,qty,fr,to,sup,ref,obs in pending:
            create_movement(typ,pid,qty,fr,to,sup,ref,obs,d)
        st.success("Cierre y movimientos pendientes guardados correctamente.")

elif page=='Recibir pedido':
    st.title("📦 Recibir pedido")
    st.caption("Opción adicional: úsala si puedes registrar el pedido cuando llega. Si no, podrá ingresarse más tarde desde apertura/cierre.")
    d=st.date_input("Fecha de recepción",value=date.today()); supplier=st.text_input("Proveedor"); ref=st.text_input("Factura / referencia (opcional)")
    wh=one("SELECT id FROM locations WHERE name='Bodega'")['id']; bar=one("SELECT id FROM locations WHERE name='Bar'")['id']
    dest_name=st.selectbox("Destino",['Bodega','Bar'],index=0,disabled=user['role']=='STAFF')
    dest=wh if dest_name=='Bodega' else bar
    ps=[p for p in products() if p['category'] in ('Cerveza','Licor')]; n=int(st.number_input("Número de productos recibidos",1,50,1)); mp={product_label(p):p for p in ps}; rows=[]
    for i in range(n):
        nm=st.selectbox(f"Producto {i+1}",list(mp),key=f'rp{i}'); p=mp[nm]; qty=movement_qty_input(p,f'rq{i}')
        obs=st.text_input(f"Observación {i+1} (opcional)",key=f'ro{i}')
        if qty>0: rows.append((p['id'],qty,obs))
    if st.button("Confirmar recepción",type="primary",use_container_width=True):
        if not rows: st.error("Ingresa al menos una cantidad mayor que cero.")
        else:
            for pid,qty,obs in rows: create_movement('SUPPLIER',pid,qty,None,dest,supplier,ref,obs,d)
            st.success(f"Recepción registrada en {dest_name}.")

elif page=='Trasladar productos':
    st.title("↔️ Trasladar productos")
    st.caption("Opción adicional para registrar un traslado en el momento. Si no hay tiempo, puede registrarse después como movimiento pendiente.")
    d=st.date_input("Fecha del traslado",value=date.today()); wh=one("SELECT id FROM locations WHERE name='Bodega'")['id']; bar=one("SELECT id FROM locations WHERE name='Bar'")['id']
    ps=[p for p in products() if p['category'] in ('Cerveza','Licor')]; n=int(st.number_input("Número de productos trasladados",1,50,1)); mp={product_label(p):p for p in ps}; rows=[]
    for i in range(n):
        nm=st.selectbox(f"Producto {i+1}",list(mp),key=f'tp{i}'); p=mp[nm]; qty=movement_qty_input(p,f'tq{i}')
        if qty>0: rows.append((p['id'],qty))
    if st.button("Confirmar traslado Bodega → Bar",type="primary",use_container_width=True):
        if not rows: st.error("Ingresa al menos una cantidad mayor que cero.")
        else:
            for pid,qty in rows: create_movement('TRANSFER',pid,qty,wh,bar,d=d)
            st.success("Traslado registrado.")

elif page=='POS / Ventas':
    st.title("POS / Ventas")
    st.caption("Puedes registrar ventas por día. La carga masiva desde Excel se encuentra en Administración.")
    d=st.date_input("Fecha de ventas",value=date.today()); typ=st.selectbox("Tipo",['Cóctel','Shot','Cerveza','Botella de licor'])
    cid=pid=None; ozunit=None
    if typ=='Cóctel':
        items=q("SELECT * FROM cocktails WHERE active=1 ORDER BY name"); mp={r['name']:r['id'] for r in items}; nm=st.selectbox("Cóctel",list(mp) if mp else ['— Sin cócteles —']); cid=mp.get(nm)
    else:
        cat='Cerveza' if typ=='Cerveza' else 'Licor'; items=products(cat); mp={product_label(r):r for r in items}; nm=st.selectbox("Producto",list(mp) if mp else ['— Sin productos —']); p=mp.get(nm); pid=p['id'] if p else None
        if typ=='Shot': ozunit=st.number_input("Oz por shot",min_value=.25,step=.25,value=1.0)
    qty=st.number_input("Unidades vendidas",min_value=0.0,step=1.0); obs=st.text_input("Observación (opcional)")
    if st.button("Guardar venta",type="primary"):
        if qty<=0 or not (cid or pid): st.error("Completa la venta.")
        else:
            ex("INSERT INTO pos_sales(sale_date,cocktail_id,product_id,sale_type,quantity,oz_per_unit,user_id,observation,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
               (d.isoformat(),cid,pid,typ,qty,ozunit,user['id'],obs,now_iso()))
            st.success("Venta guardada.")

elif page=='Dashboard':
    st.title("Dashboard consolidado")
    a,b=st.columns(2); d1=a.date_input("Desde",value=date.today()-timedelta(days=6),key='dash1'); d2=b.date_input("Hasta",value=date.today(),key='dash2')
    if d2<d1: st.error("La fecha final no puede ser anterior a la inicial."); st.stop()
    data=consolidated(d1,d2)
    with_data=[r for r in data if r['Días completos']>0 or r['Consumo esperado']>0 or r['Ajustes']>0 or r['Alertas apertura']>0]
    alerts=sum(1 for r in with_data if r['Estado']!='✅ OK'); ok=sum(1 for r in with_data if r['Estado']=='✅ OK')
    worst=max(with_data,key=lambda r:abs(r['Diferencia no explicada']),default=None)
    x1,x2,x3,x4=st.columns(4); x1.metric("Productos controlados",len(with_data)); x2.metric("Sin alertas",ok); x3.metric("Con alerta",alerts); x4.metric("Mayor diferencia",f"{worst['Producto']}: {worst['Diferencia no explicada']:+.2f}" if worst else "—")
    st.caption("Consumo real = apertura + entradas al Bar − cierre. Diferencia no explicada = consumo real − (consumo esperado por POS + pruebas/desperdicios/cortesías).")
    show=[]
    for r in with_data:
        show.append({k:r[k] for k in ['Producto','Categoría','Inicial','Final','Entradas al bar','Consumo real','Consumo esperado','Ajustes','Diferencia no explicada','Alertas apertura','Estado']})
    if show: st.dataframe(pd.DataFrame(show),use_container_width=True,hide_index=True)
    else: st.info("No hay días completos de apertura+cierre ni ventas/ajustes en este rango.")
    st.divider(); st.subheader("Detalle para auditoría")
    mode=st.selectbox("Mostrar",['Solo alertas de apertura','Aperturas','Cierres','Ambos'])
    if mode=='Solo alertas de apertura':
        df=pd.read_sql_query("""SELECT s.session_date Fecha,p.name Producto,ROUND(ic.previous_qty,2) 'Cierre anterior',ROUND(ic.qty_base,2) Apertura,ROUND(ic.variance,2) Diferencia,ic.observation Observación,u.name Empleado
                              FROM inventory_counts ic JOIN inventory_sessions s ON s.id=ic.session_id JOIN products p ON p.id=ic.product_id JOIN users u ON u.id=s.user_id
                              WHERE s.session_type='OPENING' AND s.session_date BETWEEN ? AND ? AND ABS(COALESCE(ic.variance,0))>0 ORDER BY s.session_date DESC,p.name""",con,params=(d1.isoformat(),d2.isoformat()))
    else:
        types={'Aperturas':['OPENING'],'Cierres':['CLOSING'],'Ambos':['OPENING','CLOSING']}[mode]; placeholders=','.join('?'*len(types))
        df=pd.read_sql_query(f"""SELECT s.session_date Fecha,s.session_type Tipo,p.name Producto,ROUND(ic.qty_base,2) Conteo,ic.observation Observación,u.name Empleado
                              FROM inventory_counts ic JOIN inventory_sessions s ON s.id=ic.session_id JOIN products p ON p.id=ic.product_id JOIN users u ON u.id=s.user_id
                              WHERE s.session_date BETWEEN ? AND ? AND s.session_type IN ({placeholders}) ORDER BY s.session_date DESC,s.session_type,p.name""",con,params=(d1.isoformat(),d2.isoformat(),*types))
    st.dataframe(df,use_container_width=True,hide_index=True)

elif page=='Abastecimiento':
    st.title("📦 Abastecimiento semanal")
    st.caption("Recomendación de compra basada en consumo real reciente, stock disponible y stock de seguridad.")
    lookback=int(st.selectbox("Histórico para estimar consumo",[14,21,28,42,56],index=2,format_func=lambda x:f"Últimos {x} días")); safety=float(setting('safety_stock_pct','15'))/100
    d2=date.today(); d1=d2-timedelta(days=lookback-1); data=consolidated(d1,d2); bar=one("SELECT id FROM locations WHERE name='Bar'")['id']; wh=one("SELECT id FROM locations WHERE name='Bodega'")['id']
    rows=[]
    for r in data:
        p=r['_p']; complete=max(r['Días completos'],0)
        weekly=(r['Consumo real']/complete*7) if complete else 0
        target=weekly*(1+safety); sb=current_stock(p['id'],bar); sw=current_stock(p['id'],wh); stock=max(sb+sw,0); need=max(target-stock,0)
        if p['category']=='Licor' and p['bottle_ml']:
            bottle_oz=float(p['bottle_ml'])/ML_PER_OZ; bottles=math.ceil(need/bottle_oz) if need>0 else 0
        else: bottles=math.ceil(need) if need>0 else 0
        rows.append({'Producto':product_label(p),'Consumo semanal estimado':round(weekly,2),'Stock Bar':round(sb,2),'Stock Bodega':round(sw,2),'Stock total':round(stock,2),'Stock seguridad %':int(safety*100),'Comprar (botellas/unidades)':bottles,'Días usados':complete})
    df=pd.DataFrame(rows)
    df=df[(df['Días usados']>0) | (df['Stock total']>0)].sort_values(['Comprar (botellas/unidades)','Producto'],ascending=[False,True])
    if len(df): st.dataframe(df,use_container_width=True,hide_index=True)
    else: st.info("Aún no hay suficiente información para estimar abastecimiento.")
    st.caption("Para licores sin presentación en ml, la recomendación es provisional porque no se puede convertir oz a botellas con precisión.")

elif page=='Reporte PDF':
    st.title("Reporte PDF")
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
    st.title("Administración")
    t1,t2,t3,t4,t5=st.tabs(['Productos','Cócteles / Recetas','Usuarios','Importar Excel','Configuración'])
    with t1:
        st.subheader("Agregar / actualizar producto")
        cats=q("SELECT * FROM categories WHERE name IN ('Cerveza','Licor') ORDER BY name"); cm={r['name']:r['id'] for r in cats}; cat=st.selectbox("Categoría",list(cm)); name=st.text_input("Nombre del producto"); ml=st.number_input("Presentación (ml)",min_value=0.0,value=0.0,step=5.0); pkg=st.selectbox("Envase",['Botella','Lata','Otro'])
        if st.button("Agregar producto",type="primary") and name.strip():
            try:
                ex("INSERT INTO products(category_id,name,bottle_ml,package_type) VALUES(?,?,?,?)",(cm[cat],name.strip(),ml or None,pkg)); st.success("Producto agregado."); st.rerun()
            except sqlite3.IntegrityError: st.error("Ese producto con la misma presentación ya existe.")
        st.caption("Los productos importados del Google Sheet no tenían presentación en ml. Complétala aquí para distinguir presentaciones y convertir licores a botellas correctamente.")
        df=pd.read_sql_query("SELECT p.id ID,c.name Categoría,p.name Producto,p.bottle_ml 'ml',p.package_type Envase,p.active Activo FROM products p JOIN categories c ON c.id=p.category_id ORDER BY c.name,p.name",con)
        st.dataframe(df,use_container_width=True,hide_index=True)
        pid=st.number_input("ID del producto a actualizar",min_value=1,step=1); newml=st.number_input("Nuevo ml",min_value=0.0,step=5.0,key='updml')
        if st.button("Actualizar presentación"):
            ex("UPDATE products SET bottle_ml=? WHERE id=?",(newml or None,int(pid))); st.success("Presentación actualizada."); st.rerun()
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
        st.dataframe(pd.read_sql_query("SELECT c.name Cóctel,p.name Licor,r.oz_qty 'Oz por cóctel' FROM recipes r JOIN cocktails c ON c.id=r.cocktail_id JOIN products p ON p.id=r.product_id ORDER BY c.name,p.name",con),use_container_width=True,hide_index=True)
    with t3:
        st.subheader("Usuarios autorizados")
        st.caption("Solo los correos de esta lista con estado Activo pueden entrar con Google. Compartir el enlace no da acceso.")
        email=st.text_input("Correo Google / Gmail").strip().lower()
        un=st.text_input("Nombre del usuario")
        role=st.selectbox("Rol",['STAFF','MANAGER','ADMIN'])
        if st.button("Autorizar usuario",type="primary",use_container_width=True):
            if not email or '@' not in email:
                st.error("Ingresa un correo válido.")
            else:
                existing=one("SELECT * FROM users WHERE lower(email)=?",(email,))
                if existing:
                    ex("UPDATE users SET name=?,role=?,active=1 WHERE id=?",(un.strip() or existing['name'],role,existing['id']))
                    st.success("Usuario actualizado y activado."); st.rerun()
                else:
                    base_name=un.strip() or email.split('@')[0]
                    candidate=base_name; i=2
                    while one("SELECT 1 FROM users WHERE name=?",(candidate,)):
                        candidate=f"{base_name} {i}"; i+=1
                    ex("INSERT INTO users(name,pin_hash,email,role,active,created_at) VALUES(?,?,?,?,1,?)",(candidate,'',email,role,now_iso()))
                    st.success("Correo autorizado. Ya puede entrar con Google."); st.rerun()
        users_df=pd.read_sql_query("SELECT id ID,name Nombre,email Email,role Rol,CASE active WHEN 1 THEN 'Activo' ELSE 'Bloqueado' END Estado,last_login_at 'Último acceso' FROM users WHERE email IS NOT NULL AND email<>'' ORDER BY active DESC,role,name",con)
        st.dataframe(users_df,use_container_width=True,hide_index=True)
        manageable=q("SELECT id,name,email,role,active FROM users WHERE email IS NOT NULL AND email<>'' ORDER BY name")
        if manageable:
            labels={f"{r['name']} · {r['email']} · {r['role']} · {'Activo' if r['active'] else 'Bloqueado'}":r for r in manageable}
            sel=st.selectbox("Gestionar usuario",list(labels.keys()))
            target=labels[sel]
            c1,c2=st.columns(2)
            if target['active']:
                if c1.button("Bloquear acceso",use_container_width=True):
                    if target['id']==user['id']:
                        st.error("No puedes bloquear tu propia cuenta mientras estás conectado.")
                    else:
                        ex("UPDATE users SET active=0 WHERE id=?",(target['id'],)); st.success("Usuario bloqueado."); st.rerun()
            else:
                if c1.button("Reactivar acceso",use_container_width=True):
                    ex("UPDATE users SET active=1 WHERE id=?",(target['id'],)); st.success("Usuario reactivado."); st.rerun()
            new_role=c2.selectbox("Cambiar rol",['STAFF','MANAGER','ADMIN'],index=['STAFF','MANAGER','ADMIN'].index(target['role']),key='manage_role')
            if c2.button("Guardar rol",use_container_width=True):
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
        safety=st.number_input("Stock de seguridad para abastecimiento (%)",min_value=0,max_value=100,value=int(float(setting('safety_stock_pct','15'))),step=1)
        tb=st.number_input("Tolerancia cerveza (botellas)",min_value=0.0,value=float(setting('tolerance_beer','1')),step=.5)
        tl=st.number_input("Tolerancia licor (oz)",min_value=0.0,value=float(setting('tolerance_liquor','1')),step=.25)
        if st.button("Guardar configuración",type="primary"):
            for k,v in [('safety_stock_pct',safety),('tolerance_beer',tb),('tolerance_liquor',tl)]: con.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(k,str(v)))
            con.commit(); st.success("Configuración guardada.")
