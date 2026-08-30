import streamlit as st
import sqlite3, hashlib, io
from datetime import datetime, date
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

DB="bar_inventory.db"; ML_PER_OZ=29.5735295625
st.set_page_config(page_title="Bar Inventory MVP",page_icon="🍸",layout="wide")
@st.cache_resource
def db():
 c=sqlite3.connect(DB,check_same_thread=False); c.row_factory=sqlite3.Row; c.execute("PRAGMA foreign_keys=ON"); return c
con=db()
def q(s,p=()): return con.execute(s,p).fetchall()
def one(s,p=()): return con.execute(s,p).fetchone()
def ex(s,p=()): con.execute(s,p); con.commit()
def init():
 con.executescript("""
 CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT UNIQUE NOT NULL,pin_hash TEXT NOT NULL,role TEXT NOT NULL,active INTEGER DEFAULT 1);
 CREATE TABLE IF NOT EXISTS categories(id INTEGER PRIMARY KEY,name TEXT UNIQUE NOT NULL,count_unit TEXT NOT NULL);
 CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY,category_id INTEGER NOT NULL,name TEXT UNIQUE NOT NULL,bottle_ml REAL,active INTEGER DEFAULT 1,FOREIGN KEY(category_id) REFERENCES categories(id));
 CREATE TABLE IF NOT EXISTS locations(id INTEGER PRIMARY KEY,name TEXT UNIQUE NOT NULL);
 CREATE TABLE IF NOT EXISTS inventory_sessions(id INTEGER PRIMARY KEY,session_date TEXT,session_type TEXT,user_id INTEGER,created_at TEXT,submitted INTEGER DEFAULT 1,notes TEXT);
 CREATE TABLE IF NOT EXISTS inventory_counts(id INTEGER PRIMARY KEY,session_id INTEGER,product_id INTEGER,location_id INTEGER,qty_base REAL,previous_qty REAL,variance REAL,observation TEXT);
 CREATE TABLE IF NOT EXISTS movements(id INTEGER PRIMARY KEY,movement_date TEXT,movement_type TEXT,product_id INTEGER,qty_base REAL,from_location_id INTEGER,to_location_id INTEGER,user_id INTEGER,observation TEXT,created_at TEXT);
 CREATE TABLE IF NOT EXISTS cocktails(id INTEGER PRIMARY KEY,name TEXT UNIQUE NOT NULL,active INTEGER DEFAULT 1);
 CREATE TABLE IF NOT EXISTS recipes(id INTEGER PRIMARY KEY,cocktail_id INTEGER,product_id INTEGER,oz_qty REAL);
 CREATE TABLE IF NOT EXISTS pos_sales(id INTEGER PRIMARY KEY,date_from TEXT,date_to TEXT,cocktail_id INTEGER,product_id INTEGER,sale_type TEXT,quantity REAL,user_id INTEGER,created_at TEXT);
 """)
 for n,u in [("Cerveza","bottle"),("Licor","oz"),("Cócteles","sale")]: con.execute("INSERT OR IGNORE INTO categories(name,count_unit) VALUES(?,?)",(n,u))
 for n in ["Bar","Bodega"]: con.execute("INSERT OR IGNORE INTO locations(name) VALUES(?)",(n,))
 if not one("SELECT 1 FROM users"): con.execute("INSERT INTO users(name,pin_hash,role) VALUES(?,?,?)",("Admin",hashlib.sha256(b"1234").hexdigest(),"ADMIN"))
 con.commit()
init()
def products(cat=None):
 s="SELECT p.*,c.name category FROM products p JOIN categories c ON c.id=p.category_id WHERE p.active=1"; p=[]
 if cat: s+=" AND c.name=?"; p=[cat]
 return q(s+" ORDER BY p.name",p)
def last_close(pid,lid):
 r=one("SELECT ic.qty_base FROM inventory_counts ic JOIN inventory_sessions s ON s.id=ic.session_id WHERE ic.product_id=? AND ic.location_id=? AND s.session_type='CLOSING' ORDER BY s.session_date DESC,s.created_at DESC LIMIT 1",(pid,lid)); return float(r[0]) if r else 0.0
def save_session(kind,counts,notes=""):
 cur=con.execute("INSERT INTO inventory_sessions(session_date,session_type,user_id,created_at,notes) VALUES(?,?,?,?,?)",(date.today().isoformat(),kind,user['id'],datetime.now().isoformat(timespec='seconds'),notes)); sid=cur.lastrowid
 for x in counts: con.execute("INSERT INTO inventory_counts(session_id,product_id,location_id,qty_base,previous_qty,variance,observation) VALUES(?,?,?,?,?,?,?)",(sid,x['pid'],x['lid'],x['qty'],x.get('prev'),x.get('var'),x.get('obs')))
 con.commit()
def count_input(p,key,default=0.0):
 if p['category']=='Cerveza': return float(st.number_input("Botellas",min_value=0,value=int(round(default)),step=1,key=key))
 if not p['bottle_ml']: return st.number_input("Total oz",min_value=0.0,value=float(default),step=.25,key=key)
 oz=p['bottle_ml']/ML_PER_OZ; full=int(default//oz); rem=max(0.0,default-full*oz); a,b=st.columns(2)
 f=a.number_input("Botellas completas",min_value=0,value=full,step=1,key=key+'f'); o=b.number_input("Botella abierta (oz)",min_value=0.0,max_value=float(oz),value=float(round(rem,2)),step=.25,key=key+'o'); st.caption(f"{p['bottle_ml']:.0f} ml = {oz:.2f} oz"); return f*oz+o

def login():
 st.title("🍸 Bar Inventory"); st.caption("MVP de inventario")
 names=[r['name'] for r in q("SELECT name FROM users WHERE active=1 ORDER BY name")]; n=st.selectbox("Usuario",names); pin=st.text_input("PIN",type="password")
 if st.button("Entrar",type="primary",use_container_width=True):
  u=one("SELECT * FROM users WHERE name=?",(n,))
  if u and u['pin_hash']==hashlib.sha256(pin.encode()).hexdigest(): st.session_state.user=dict(u); st.rerun()
  else: st.error("PIN incorrecto")
 st.info("Primera prueba: Admin / PIN 1234")
if 'user' not in st.session_state: login(); st.stop()
user=st.session_state.user
with st.sidebar:
 st.markdown(f"### {user['name']}"); st.caption(user['role']); pages=['Apertura','Cierre']
 if user['role'] in ('MANAGER','ADMIN'): pages+=['POS / Ventas','Dashboard','Reporte PDF']
 if user['role']=='ADMIN': pages+=['Administración']
 page=st.radio("Menú",pages)
 if st.button("Cerrar sesión"): del st.session_state.user; st.rerun()

if page=='Apertura':
 st.title("Apertura"); st.caption("El cierre anterior está precargado. Verifica físicamente y modifica solo lo diferente.")
 bar=one("SELECT id FROM locations WHERE name='Bar'")['id']; ps=[p for p in products() if p['category'] in ('Cerveza','Licor')]; counts=[]; bad=False
 if not ps: st.warning("Agrega primero los productos reales en Administración.")
 for cat in ['Cerveza','Licor']:
  g=[p for p in ps if p['category']==cat]
  if g: st.subheader(cat)
  for p in g:
   prev=last_close(p['id'],bar)
   with st.expander(p['name'],expanded=True):
    st.metric("Cierre anterior",f"{prev:.2f} oz" if cat=='Licor' else f"{prev:.0f} botellas"); val=count_input(p,f"o{p['id']}",prev); var=val-prev; obs=''
    if abs(var)>.001:
     st.warning(f"Diferencia {var:+.2f}"); obs=st.text_input("Observación obligatoria",key=f"ob{p['id']}"); bad|=not bool(obs.strip())
    counts.append({'pid':p['id'],'lid':bar,'qty':val,'prev':prev,'var':var,'obs':obs})
 if st.button("Enviar apertura",type="primary",use_container_width=True,disabled=not ps):
  if bad: st.error("Falta una observación para una diferencia.")
  else: save_session('OPENING',counts); st.success("Apertura guardada."); st.balloons()

elif page=='Cierre':
 st.title("Cierre"); bar=one("SELECT id FROM locations WHERE name='Bar'")['id']; wh=one("SELECT id FROM locations WHERE name='Bodega'")['id']; ps=[p for p in products() if p['category'] in ('Cerveza','Licor')]; counts=[]
 if not ps: st.warning("Agrega primero los productos reales en Administración.")
 for cat in ['Cerveza','Licor']:
  g=[p for p in ps if p['category']==cat]
  if g: st.subheader(cat)
  for p in g:
   with st.expander(p['name'],expanded=True): counts.append({'pid':p['id'],'lid':bar,'qty':count_input(p,f"c{p['id']}",0)})
 st.divider(); transfers=[]
 if st.toggle("¿Hoy se trasladaron productos de bodega al bar?"):
  for p in ps:
   v=st.number_input(p['name'],min_value=0.0,step=1.0 if p['category']=='Cerveza' else .25,key=f"t{p['id']}");
   if v>0: transfers.append((p['id'],v))
 supplier=[]
 if st.toggle("¿Hoy se recibieron productos del proveedor?"):
  for p in ps:
   v=st.number_input(p['name'],min_value=0.0,step=1.0 if p['category']=='Cerveza' else .25,key=f"s{p['id']}");
   if v>0: supplier.append((p['id'],v))
 adjusts=[]
 if st.toggle("¿Hoy se realizaron pruebas, hubo desperdicios o se dieron cortesías?"):
  n=st.number_input("Número de registros",1,10,1)
  names={p['name']:p for p in ps}
  for i in range(n):
   a,b,c=st.columns([1,2,1]); typ=a.selectbox("Tipo",['Prueba','Desperdicio','Cortesía'],key=f"at{i}"); nm=b.selectbox("Producto",list(names),key=f"ap{i}") if names else None; qty=c.number_input("Cantidad",min_value=0.0,step=.25,key=f"aq{i}"); obs=st.text_input("Observación",key=f"ao{i}")
   if nm and qty>0: adjusts.append((typ.upper(),names[nm]['id'],qty,obs))
 notes=st.text_area("Observaciones generales (opcional)")
 if st.button("Enviar cierre",type="primary",use_container_width=True,disabled=not ps):
  save_session('CLOSING',counts,notes); now=datetime.now().isoformat(timespec='seconds')
  for pid,v in transfers: con.execute("INSERT INTO movements(movement_date,movement_type,product_id,qty_base,from_location_id,to_location_id,user_id,created_at) VALUES(?,?,?,?,?,?,?,?)",(date.today().isoformat(),'TRANSFER',pid,v,wh,bar,user['id'],now))
  for pid,v in supplier: con.execute("INSERT INTO movements(movement_date,movement_type,product_id,qty_base,to_location_id,user_id,created_at) VALUES(?,?,?,?,?,?,?)",(date.today().isoformat(),'SUPPLIER',pid,v,wh,user['id'],now))
  for typ,pid,v,obs in adjusts: con.execute("INSERT INTO movements(movement_date,movement_type,product_id,qty_base,from_location_id,user_id,observation,created_at) VALUES(?,?,?,?,?,?,?,?)",(date.today().isoformat(),typ,pid,v,bar,user['id'],obs,now))
  con.commit(); st.success("Cierre guardado."); st.balloons()

elif page=='POS / Ventas':
 st.title("POS / Ventas"); a,b=st.columns(2); d1=a.date_input("Desde"); d2=b.date_input("Hasta"); typ=st.selectbox("Tipo",['Cóctel','Shot','Cerveza','Botella de licor']); cid=pid=None
 if typ=='Cóctel': items=q("SELECT * FROM cocktails WHERE active=1 ORDER BY name"); mp={r['name']:r['id'] for r in items}; nm=st.selectbox("Cóctel",list(mp) if mp else ['— Sin cócteles —']); cid=mp.get(nm)
 else:
  cat='Cerveza' if typ=='Cerveza' else 'Licor'; items=products(cat); mp={r['name']:r['id'] for r in items}; nm=st.selectbox("Producto",list(mp) if mp else ['— Sin productos —']); pid=mp.get(nm)
 qty=st.number_input("Cantidad vendida",min_value=0.0,step=1.0)
 if st.button("Guardar venta",type="primary") and qty>0 and (cid or pid): ex("INSERT INTO pos_sales(date_from,date_to,cocktail_id,product_id,sale_type,quantity,user_id,created_at) VALUES(?,?,?,?,?,?,?,?)",(d1.isoformat(),d2.isoformat(),cid,pid,typ,qty,user['id'],datetime.now().isoformat(timespec='seconds'))); st.success("Venta guardada.")

elif page=='Dashboard':
 st.title("Dashboard"); a,b=st.columns(2); d1=a.date_input("Desde",key='d1'); d2=b.date_input("Hasta",key='d2')
 inv=one("SELECT COUNT(*) n FROM inventory_sessions WHERE session_date BETWEEN ? AND ?",(d1.isoformat(),d2.isoformat()))['n']; dif=one("SELECT COUNT(*) n FROM inventory_counts ic JOIN inventory_sessions s ON s.id=ic.session_id WHERE s.session_type='OPENING' AND s.session_date BETWEEN ? AND ? AND ABS(COALESCE(ic.variance,0))>.001",(d1.isoformat(),d2.isoformat()))['n']; adj=one("SELECT COALESCE(SUM(qty_base),0) n FROM movements WHERE movement_date BETWEEN ? AND ? AND movement_type IN ('PRUEBA','DESPERDICIO','CORTESÍA')",(d1.isoformat(),d2.isoformat()))['n']; sales=one("SELECT COALESCE(SUM(quantity),0) n FROM pos_sales WHERE date_from>=? AND date_to<=?",(d1.isoformat(),d2.isoformat()))['n']
 x1,x2,x3,x4=st.columns(4); x1.metric("Inventarios",inv); x2.metric("Diferencias apertura",dif); x3.metric("Pruebas/desperdicios/cortesías",f"{adj:.2f}"); x4.metric("Unidades POS",f"{sales:.0f}")
 df=pd.read_sql_query("SELECT s.session_date Fecha,s.session_type Tipo,u.name Empleado,c.name Categoria,p.name Producto,ROUND(ic.qty_base,2) Cantidad,ROUND(ic.variance,2) Diferencia,ic.observation Observación FROM inventory_counts ic JOIN inventory_sessions s ON s.id=ic.session_id JOIN users u ON u.id=s.user_id JOIN products p ON p.id=ic.product_id JOIN categories c ON c.id=p.category_id WHERE s.session_date BETWEEN ? AND ? ORDER BY s.session_date DESC",con,params=(d1.isoformat(),d2.isoformat())); st.dataframe(df,use_container_width=True,hide_index=True)

elif page=='Reporte PDF':
 st.title("Reporte PDF"); a,b=st.columns(2); d1=a.date_input("Desde",key='r1'); d2=b.date_input("Hasta",key='r2')
 if st.button("Generar PDF",type="primary"):
  buf=io.BytesIO(); doc=SimpleDocTemplate(buf,pagesize=letter); sty=getSampleStyleSheet(); story=[Paragraph("BAR INVENTORY REPORT",sty['Title']),Paragraph(f"Periodo: {d1} a {d2}",sty['Normal']),Spacer(1,12)]; data=[["Fecha","Tipo","Empleado","Producto","Cantidad","Dif."]]; rows=q("SELECT s.session_date,s.session_type,u.name,p.name,ROUND(ic.qty_base,2),ROUND(COALESCE(ic.variance,0),2) FROM inventory_counts ic JOIN inventory_sessions s ON s.id=ic.session_id JOIN users u ON u.id=s.user_id JOIN products p ON p.id=ic.product_id WHERE s.session_date BETWEEN ? AND ? ORDER BY s.session_date",(d1.isoformat(),d2.isoformat())); data += [list(r) for r in rows]; t=Table(data,repeatRows=1); t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('GRID',(0,0),(-1,-1),.25,colors.grey),('FONTSIZE',(0,0),(-1,-1),8)])); story.append(t); doc.build(story); buf.seek(0); st.download_button("Descargar reporte",buf,file_name=f"bar_inventory_{d1}_{d2}.pdf",mime="application/pdf")

elif page=='Administración':
 st.title("Administración"); t1,t2,t3=st.tabs(['Productos','Cócteles / Recetas','Usuarios'])
 with t1:
  cats=q("SELECT * FROM categories WHERE name IN ('Cerveza','Licor') ORDER BY name"); cm={r['name']:r['id'] for r in cats}; cat=st.selectbox("Categoría",list(cm)); name=st.text_input("Nombre del producto"); ml=st.number_input("Presentación ml (solo licor)",min_value=0.0,value=750.0 if cat=='Licor' else 0.0,step=50.0)
  if st.button("Agregar producto",type="primary") and name.strip():
   try: ex("INSERT INTO products(category_id,name,bottle_ml) VALUES(?,?,?)",(cm[cat],name.strip(),ml if cat=='Licor' else None)); st.success("Producto agregado."); st.rerun()
   except sqlite3.IntegrityError: st.error("Ese producto ya existe.")
  st.dataframe(pd.read_sql_query("SELECT c.name Categoría,p.name Producto,p.bottle_ml 'ml botella',p.active Activo FROM products p JOIN categories c ON c.id=p.category_id ORDER BY c.name,p.name",con),hide_index=True,use_container_width=True)
 with t2:
  cn=st.text_input("Nombre del cóctel")
  if st.button("Crear cóctel") and cn.strip():
   try: ex("INSERT INTO cocktails(name) VALUES(?)",(cn.strip(),)); st.success("Cóctel creado."); st.rerun()
   except sqlite3.IntegrityError: st.error("Ya existe.")
  cs=q("SELECT * FROM cocktails WHERE active=1 ORDER BY name"); ls=products('Licor')
  if cs and ls:
   cm={r['name']:r['id'] for r in cs}; lm={r['name']:r['id'] for r in ls}; c=st.selectbox("Cóctel",list(cm),key='rc'); l=st.selectbox("Licor",list(lm),key='rl'); oz=st.number_input("Oz por cóctel",min_value=0.0,step=.25,value=1.0)
   if st.button("Agregar ingrediente") and oz>0: ex("INSERT INTO recipes(cocktail_id,product_id,oz_qty) VALUES(?,?,?)",(cm[c],lm[l],oz)); st.success("Ingrediente agregado.")
  st.dataframe(pd.read_sql_query("SELECT c.name Cóctel,p.name Licor,r.oz_qty 'Oz por cóctel' FROM recipes r JOIN cocktails c ON c.id=r.cocktail_id JOIN products p ON p.id=r.product_id ORDER BY c.name",con),hide_index=True,use_container_width=True)
 with t3:
  un=st.text_input("Nombre"); pin=st.text_input("PIN nuevo",type="password"); role=st.selectbox("Rol",['STAFF','MANAGER','ADMIN'])
  if st.button("Agregar usuario") and un.strip() and pin:
   try: ex("INSERT INTO users(name,pin_hash,role) VALUES(?,?,?)",(un.strip(),hashlib.sha256(pin.encode()).hexdigest(),role)); st.success("Usuario creado."); st.rerun()
   except sqlite3.IntegrityError: st.error("El usuario ya existe.")
  st.dataframe(pd.read_sql_query("SELECT name Nombre,role Rol,active Activo FROM users",con),hide_index=True,use_container_width=True)
