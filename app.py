import os, re, secrets, sqlite3, urllib.parse
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
import folium
from geopy.distance import geodesic
from streamlit_folium import st_folium

try:
    from streamlit_geolocation import streamlit_geolocation
    GPS_OK = True
except Exception:
    GPS_OK = False

# Urdu: App ki basic settings yahan set ki ja rahi hain.
st.set_page_config(page_title="IZZAT CIRCLE", page_icon="🤝", layout="wide")
DB = "izzat_circle.db"
UPLOADS = "uploads"
os.makedirs(UPLOADS, exist_ok=True)
AREAS = ["Raja Bazar", "Saddar", "Commercial Market", "Satellite Town", "Chaklala", "Committee Chowk", "Murree Road", "Peshawar Road", "6th Road", "Islamabad", "I-8", "G-9", "Other"]
BAZAARS = ["Raja Bazar", "Anarkali", "Urdu Bazar", "Jodia Bazar"]
AREA_COORDS = {"Raja Bazar":(33.6007,73.0479),"Saddar":(33.5969,73.0545),"Commercial Market":(33.6440,73.0820),"Satellite Town":(33.6460,73.0735),"Chaklala":(33.6168,73.0992),"Committee Chowk":(33.6087,73.0670),"Murree Road":(33.6250,73.0700),"Peshawar Road":(33.6105,73.0255),"6th Road":(33.6428,73.0710),"Islamabad":(33.6844,73.0479),"I-8":(33.6650,73.0720),"G-9":(33.6880,73.0390),"Other":(33.6844,73.0479)}

# Urdu: Green, golden aur light UI ka design yahan apply kiya ja raha hai.
st.markdown("""
<style>
.stApp{background:#f6fbf7;color:#183323}.stApp p,.stApp label,.stApp h1,.stApp h2,.stApp h3,.stApp h4{color:#183323!important}
[data-testid="stSidebar"]{background:#075c34}.brand{text-align:center;color:#075c34;font-weight:900;font-size:clamp(30px,6vw,48px)}
.slogan{text-align:center;color:#a27609;font-weight:800;font-size:18px}.mission{background:#075c34;color:white;border:2px solid #c99b2e;border-radius:14px;padding:13px;text-align:center;font-weight:900;margin:12px 0}
.card{background:white;border:1px solid #d4e3d8;border-top:4px solid #075c34;border-radius:14px;padding:15px;box-shadow:0 2px 10px #0000000d}.gold{color:#a27609!important;font-weight:900}.alert{background:#fff0f0;border:2px solid #c40000;color:#a00000;padding:13px;border-radius:12px;font-weight:900}
div[data-baseweb="input"]>div,div[data-baseweb="textarea"]>div,div[data-baseweb="select"]>div{background:#fff!important;color:#183323!important;border-color:#bdd0c2!important}input,textarea{background:#fff!important;color:#183323!important;-webkit-text-fill-color:#183323!important}
</style>
""", unsafe_allow_html=True)

# Urdu: SQLite database ki tamam required tables automatically create ki ja rahi hain.
def init_db():
    with sqlite3.connect(DB) as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,phone TEXT UNIQUE NOT NULL,name TEXT,area TEXT,user_type TEXT DEFAULT 'Aam Admi',izzat_points INTEGER DEFAULT 0,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS help_requests(id INTEGER PRIMARY KEY AUTOINCREMENT,requester_phone TEXT NOT NULL,problem TEXT NOT NULL,latitude REAL NOT NULL,longitude REAL NOT NULL,urgency TEXT NOT NULL,request_type TEXT DEFAULT 'Help',status TEXT DEFAULT 'Open',created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS bazar_items(id INTEGER PRIMARY KEY AUTOINCREMENT,seller_phone TEXT NOT NULL,item TEXT NOT NULL,price REAL NOT NULL,image_path TEXT,area TEXT NOT NULL,latitude REAL,longitude REAL,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS boli_requests(id INTEGER PRIMARY KEY AUTOINCREMENT,buyer_phone TEXT NOT NULL,product_name TEXT NOT NULL,quantity INTEGER NOT NULL,bazaar TEXT NOT NULL,budget REAL NOT NULL,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY AUTOINCREMENT,customer_phone TEXT NOT NULL,product_name TEXT NOT NULL,price REAL NOT NULL,quantity INTEGER NOT NULL,address TEXT NOT NULL,status TEXT DEFAULT 'New',created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS offers(id INTEGER PRIMARY KEY AUTOINCREMENT,boli_request_id INTEGER NOT NULL,seller_phone TEXT NOT NULL,rate REAL NOT NULL,comment TEXT,reported INTEGER DEFAULT 0,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS poster_orders(id INTEGER PRIMARY KEY AUTOINCREMENT,phone TEXT NOT NULL,name TEXT NOT NULL,university TEXT NOT NULL,poster_type TEXT NOT NULL,details TEXT NOT NULL,file_path TEXT,created_at TEXT NOT NULL);
        """)

# Urdu: Database se data DataFrame mein load kiya ja raha hai.
def q(sql, params=()):
    with sqlite3.connect(DB) as c: return pd.read_sql_query(sql,c,params=params)

# Urdu: Database mein INSERT, UPDATE ya DELETE operation execute kiya ja raha hai.
def x(sql, params=()):
    with sqlite3.connect(DB) as c:
        cur=c.execute(sql,params); c.commit(); return cur.lastrowid

# Urdu: Current time ka simple timestamp banaya ja raha hai.
def now(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Urdu: Phone ko WhatsApp ke 92 format mein convert kiya ja raha hai.
def phone92(phone):
    d=re.sub(r"\D","",str(phone)); d=d[2:] if d.startswith("92") else d; d=d[4:] if d.startswith("0092") else d; d=d[1:] if d.startswith("0") else d; return "92"+d if d else ""

# Urdu: WhatsApp notification ka clickable wa.me link banaya ja raha hai.
def wa(phone,text): return "https://wa.me/"+phone92(phone)+"?text="+urllib.parse.quote(text)

# Urdu: User profile save ya update ki ja rahi hai.
def save_user(phone,name,area,user_type):
    x("""INSERT INTO users(phone,name,area,user_type,created_at) VALUES(?,?,?,?,?) ON CONFLICT(phone) DO UPDATE SET name=excluded.name,area=excluded.area,user_type=excluded.user_type""",(phone,name,area,user_type,now()))

# Urdu: User ka record database se liya ja raha hai.
def user(phone):
    d=q("SELECT * FROM users WHERE phone=?",(phone,)); return None if d.empty else d.iloc[0].to_dict()

# Urdu: User ke Izzat Points nikale ja rahe hain.
def points(phone):
    u=user(phone); return int(u["izzat_points"] or 0) if u else 0

# Urdu: Izzat Points ko plus ya minus kiya ja raha hai.
def add_points(phone,n): x("UPDATE users SET izzat_points=MAX(0,izzat_points+?) WHERE phone=?",(int(n),phone))

# Urdu: 5 se zyada points wala user Helper hota hai.
def helper(phone): return points(phone)>5

# Urdu: Do GPS locations ka geodesic distance kilometers mein nikala ja raha hai.
def km(a,b,c,d):
    try:return geodesic((float(a),float(b)),(float(c),float(d))).km
    except:return 999999

# Urdu: Browser GPS component se user ki live location li ja rahi hai.
def gps():
    if not GPS_OK:return None,None
    try:
        r=streamlit_geolocation(key="gps_widget")
        if r and r.get("latitude") is not None:return float(r["latitude"]),float(r["longitude"])
    except:pass
    return None,None

# Urdu: Folium map par markers aur user ke click ko handle kiya ja raha hai.
def map_view(key,lat=33.6844,lon=73.0479,markers=None,zoom=13):
    m=folium.Map(location=[lat,lon],zoom_start=zoom,control_scale=True,tiles="OpenStreetMap")
    for z in markers or []:
        folium.Marker([z["lat"],z["lon"]],tooltip=z.get("tip","Details"),popup=folium.Popup(z.get("popup",""),max_width=350),icon=folium.Icon(color=z.get("color","green"),icon=z.get("icon","info-sign"))).add_to(m)
    r=st_folium(m,width=None,height=500,key=key)
    p=r.get("last_clicked") if r else None
    return (float(p["lat"]),float(p["lng"])) if p else (None,None)

# Urdu: Header mein IZZAT CIRCLE ka naam, slogan aur mission show kiya ja raha hai.
def header():
    st.markdown('<div class="brand">🤝 IZZAT CIRCLE</div><div class="slogan">Madad karo, Izzat pao</div><div class="mission">Hamara Mission: Pehle Izzat, Phir Deal</div>',unsafe_allow_html=True)

# Urdu: OTP login ke liye 6 digit code generate aur verify kiya ja raha hai.
def login():
    header(); st.subheader("📱 Phone OTP Login")
    p=st.text_input("Phone Number",placeholder="03XXXXXXXXX")
    if st.button("📲 6-Digit OTP Generate Karein",use_container_width=True):
        clean=phone92(p)
        if len(clean)!=12: st.error("Valid Pakistani mobile number enter karein.")
        else:
            st.session_state.otp=f"{secrets.randbelow(1000000):06d}"; st.session_state.otp_phone=clean; st.session_state.otp_until=datetime.now()+timedelta(minutes=5); st.rerun()
    if st.session_state.get("otp"):
        st.info(f"🔐 Demo OTP: **{st.session_state.otp}** — 5 minutes valid")
        code=st.text_input("OTP",max_chars=6)
        if st.button("✅ Verify & Login",use_container_width=True):
            if datetime.now()>st.session_state.otp_until: st.error("OTP expire ho gaya.")
            elif code==st.session_state.otp and phone92(p)==st.session_state.otp_phone:
                st.session_state.logged=st.session_state.otp_phone; st.session_state.pop("otp",None); st.rerun()
            else: st.error("OTP incorrect hai.")
    st.caption("Demo OTP local screen par show hota hai. Real SMS OTP ke liye SMS provider/API required hota hai.")

# Urdu: Pehli login ke baad user ki name, area aur type profile save ki ja rahi hai.
def profile():
    p=st.session_state.logged; u=user(p)
    if u and u.get("name"): return True
    header(); st.subheader("👤 Profile Complete Karein")
    with st.form("profile"):
        n=st.text_input("Naam"); a=st.selectbox("Area",AREAS); t=st.radio("User Type",["Aam Admi","Supplier/Helper"]); ok=st.form_submit_button("Profile Save Karein")
    if ok:
        if not n.strip(): st.error("Naam required hai.")
        else: save_user(p,n.strip(),a,t); st.success("Profile save ho gayi."); st.rerun()
    return False

# Urdu: Home par paanch concepts aur Mohalla Heroes ki top list show ki ja rahi hai.
def home():
    header(); st.title("🌿 Mohalla Community")
    cards=[("🤝","MOHALLA HELP","Ek Dosre Kaam Aao"),("🍚","DONATION","Rat Ko Koi Bhuka Na Soye"),("🛍️","MOHALLA BAZAR","Apno Se Khareedo"),("💰","BARE BAZAR BOLI","Seedhi Boli, Seedha Rate"),("⭐","IZZAT CIRCLE SYSTEM","Helper Ko Izzat Aur Priority")]
    cs=st.columns(5)
    for c,(i,t,d) in zip(cs,cards):
        with c: st.markdown(f'<div class="card"><h3>{i} {t}</h3><p>{d}</p></div>',unsafe_allow_html=True)
    st.divider(); st.subheader("🏆 Mohalla Heroes — Top 5")
    h=q("SELECT name,area,izzat_points FROM users WHERE izzat_points>5 ORDER BY izzat_points DESC LIMIT 5")
    if h.empty: st.info("Abhi Heroes list empty hai. Help karke Izzat Points earn karein.")
    else:
        cs=st.columns(min(5,len(h)))
        for i,(_,r) in enumerate(h.iterrows()):
            with cs[i]: st.markdown(f'<div class="card"><b>#{i+1} 🤝 {r.name}</b><p>{r.area}</p><span class="gold">⭐ {int(r.izzat_points)} Points</span></div>',unsafe_allow_html=True)
    st.divider(); st.subheader("✨ IZZAT CIRCLE Extras")
    a,b,c=st.columns(3)
    with a:
        if st.button("🛒 IZZAT CIRCLE Shop",use_container_width=True): st.session_state.extra="shop"
    with b:
        if st.button("🎨 Poster Service",use_container_width=True): st.session_state.extra="poster"
    with c:
        if st.button("📁 Portfolio",use_container_width=True): st.session_state.extra="portfolio"
    if st.session_state.get("extra")=="shop": shop()
    elif st.session_state.get("extra")=="poster": poster()
    elif st.session_state.get("extra")=="portfolio": portfolio()
    st.divider(); st.subheader("📍 Strong Live Map")
    la,lo=gps();
    if st.button("📍 Meri Location",use_container_width=True): st.rerun()
    if la is not None: st.success(f"GPS: {la:.6f}, {lo:.6f}")
    community_map("home_map",la,lo)

# Urdu: Helpers, suppliers aur donation points ko alag toggleable layers mein map par dikhaya ja raha hai.
def community_map(key,la=None,lo=None):
    m=folium.Map(location=[la or 33.6844,lo or 73.0479],zoom_start=12,tiles="OpenStreetMap")
    hg=folium.FeatureGroup(name="🤝 Helpers",show=True); sg=folium.FeatureGroup(name="🏪 Suppliers",show=True); dg=folium.FeatureGroup(name="🍚 Donation Points",show=True)
    u=q("SELECT name,phone,area,izzat_points FROM users WHERE izzat_points>5")
    for _,r in u.iterrows():
        a=AREA_COORDS.get(r.area,AREA_COORDS["Other"]); link=wa(r.phone,f"Assalam-o-Alaikum {r.name}, IZZAT CIRCLE se rabta kar raha hoon."); pop=f"<b>🤝 {r.name}</b><br>Area: {r.area}<br>⭐ Izzat: {int(r.izzat_points)}<br>Phone: {r.phone}<br><a href='{link}' target='_blank'>WhatsApp Pe Rabta</a>"; folium.Marker(a,tooltip=f"Helper: {r.name}",popup=folium.Popup(pop,max_width=300),icon=folium.Icon(color="green",icon="heart")).add_to(hg)
    it=q("SELECT b.*,u.name seller_name,u.izzat_points FROM bazar_items b LEFT JOIN users u ON u.phone=b.seller_phone WHERE b.latitude IS NOT NULL")
    for _,r in it.iterrows():
        link=wa(r.seller_phone,f"Assalam-o-Alaikum, {r.item} ke liye IZZAT CIRCLE par rabta kar raha hoon."); pop=f"<b>🏪 {r.item}</b><br>Seller: {r.seller_name}<br>⭐ Izzat: {int(r.izzat_points or 0)}<br><a href='{link}' target='_blank'>WhatsApp Pe Rabta</a>"; folium.Marker([r.latitude,r.longitude],tooltip=r.item,popup=folium.Popup(pop,max_width=300),icon=folium.Icon(color="blue",icon="shopping-cart")).add_to(sg)
    d=q("SELECT h.*,u.name FROM help_requests h LEFT JOIN users u ON u.phone=h.requester_phone WHERE h.request_type='Donation' AND h.status='Open'")
    for _,r in d.iterrows():
        link=wa(r.requester_phone,"Assalam-o-Alaikum, IZZAT CIRCLE donation request ke liye rabta kar raha hoon."); pop=f"<b>🍚 Donation Needed</b><br>{r.problem}<br>Urgency: {r.urgency}<br><a href='{link}' target='_blank'>WhatsApp Pe Rabta</a>"; folium.Marker([r.latitude,r.longitude],tooltip="Donation Point",popup=folium.Popup(pop,max_width=300),icon=folium.Icon(color="orange",icon="gift")).add_to(dg)
    if la is not None: folium.Marker([la,lo],tooltip="Meri Location",icon=folium.Icon(color="red",icon="user")).add_to(m)
    hg.add_to(m);sg.add_to(m);dg.add_to(m);folium.LayerControl(collapsed=False).add_to(m);st_folium(m,width=None,height=520,key=key)

# Urdu: Mohalla Help aur Donation requests create karke 2KM ke andar filter ki ja rahi hain.
def help_page():
    header(); st.header("🤝 MOHALLA HELP + DONATION"); st.caption("Ek Dosre Kaam Aao • 2KM nearby filter")
    la,lo=gps();
    if st.button("📍 Meri Location",key="help_gps",use_container_width=True): st.rerun()
    with st.form("help_form"):
        problem=st.text_area("Problem / Zaroorat"); urgency=st.selectbox("Urgency",["Normal","Important","Urgent"]); typ=st.radio("Request Type",["Help","Donation"]); ok=st.form_submit_button("📢 Request Post Karein")
    cla,clo=map_view("help_pin",la or 33.6844,lo or 73.0479,zoom=13); sla=cla if cla is not None else la; slo=clo if clo is not None else lo
    if ok:
        if not problem.strip(): st.error("Problem required hai.")
        elif sla is None: st.error("Meri Location ya map click se location select karein.")
        else: x("INSERT INTO help_requests(requester_phone,problem,latitude,longitude,urgency,request_type,created_at) VALUES(?,?,?,?,?,?,?)",(st.session_state.logged,problem.strip(),sla,slo,urgency,typ,now()));st.success("✅ Request save ho gayi.");st.rerun()
    st.divider(); st.subheader("📍 Nearby Requests — 2KM")
    if la is None: st.warning("Nearby filter ke liye GPS location enable karein."); return
    d=q("SELECT h.*,u.name,u.area FROM help_requests h LEFT JOIN users u ON u.phone=h.requester_phone WHERE h.status='Open' ORDER BY h.id DESC")
    for _,r in d.iterrows():
        dist=km(la,lo,r.latitude,r.longitude)
        if dist>2: continue
        link=wa(r.requester_phone,f"Assalam-o-Alaikum, IZZAT CIRCLE par aapki request '{r.problem}' ke liye help karna chahta hoon.")
        with st.container(border=True):
            st.markdown(f"### {'🚨' if r.urgency=='Urgent' else '🤝'} {r.problem}"); st.write(f"**Area:** {r.area} • **Distance:** {dist:.2f}KM • **Urgency:** {r.urgency}")
            st.markdown(f"[📲 WhatsApp Pe Rabta]({link})")
            if r.request_type=="Help" and r.requester_phone!=st.session_state.logged:
                if st.button("🤝 Main Help Karunga",key=f"accept_{r.id}"):
                    x("UPDATE help_requests SET status='In Progress' WHERE id=?",(int(r.id),)); add_points(st.session_state.logged,1); st.success("Help accept ho gayi. WhatsApp se requester ko contact karein."); st.rerun()

# Urdu: Mohalla Bazar mein seller item add aur customer ke 3KM products show kiye ja rahe hain.
def bazar_page():
    header(); st.header("🛍️ MOHALLA BAZAR"); st.caption("Apno Se Khareedo • 3KM radius")
    la,lo=gps();
    with st.form("item_form"):
        item=st.text_input("Item"); price=st.number_input("Price (Rs.)",min_value=1.0,step=10.0); area=st.selectbox("Area",AREAS); img=st.file_uploader("Image",type=["png","jpg","jpeg","webp"]); ok=st.form_submit_button("🛍️ Item Publish Karein")
    if ok:
        n=q("SELECT COUNT(*) n FROM bazar_items WHERE seller_phone=?",(st.session_state.logged,)).iloc[0].n
        if int(n)>=3: st.error("Maximum 3 items list kar sakte hain.")
        elif not item.strip(): st.error("Item required hai.")
        else:
            path=""
            if img:
                path=os.path.join(UPLOADS,secrets.token_hex(5)+"_"+re.sub(r"[^a-zA-Z0-9_.-]","_",img.name)); open(path,"wb").write(img.getbuffer())
            x("INSERT INTO bazar_items(seller_phone,item,price,image_path,area,latitude,longitude,created_at) VALUES(?,?,?,?,?,?,?,?)",(st.session_state.logged,item.strip(),price,path,area,la,lo,now()));st.success("✅ Item publish ho gaya.");st.rerun()
    area_filter=st.selectbox("Filter by Area",["All"]+AREAS); items=q("SELECT b.*,u.name seller_name,u.izzat_points FROM bazar_items b LEFT JOIN users u ON u.phone=b.seller_phone ORDER BY b.id DESC")
    if area_filter!="All": items=items[items.area==area_filter]
    near=[]
    for _,r in items.iterrows():
        if la is not None and pd.notna(r.latitude) and pd.notna(r.longitude):
            d=km(la,lo,r.latitude,r.longitude)
            if d<=3: near.append((r,d))
        elif la is None: near.append((r,None))
    if la is not None: map_view("bazar_map",la,lo,[{"lat":r.latitude,"lon":r.longitude,"tip":r.item,"popup":f"<b>{r.item}</b><br>⭐ Izzat: {int(r.izzat_points or 0)}"} for r,d in near if pd.notna(r.latitude)],13)
    cs=st.columns(2)
    for i,(r,d) in enumerate(near):
        with cs[i%2]:
            with st.container(border=True):
                if r.image_path and os.path.exists(r.image_path): st.image(r.image_path,use_container_width=True)
                st.markdown(f"### 🛍️ {r.item}"); st.write(f"**Seller:** {r.seller_name}"); st.write(f"**Price:** Rs. {r.price:,.0f}"); st.markdown(f'<span class="gold">⭐ Seller Izzat Score: {int(r.izzat_points or 0)}</span>',unsafe_allow_html=True); st.write(f"**Area:** {r.area}"+(f" • **{d:.2f}KM**" if d is not None else "")); st.markdown(f"[📲 Order on WhatsApp]({wa(r.seller_phone,f'Assalam-o-Alaikum, {r.item} ke liye IZZAT CIRCLE par order karna hai.')})")

# Urdu: Bare Bazar Boli mein buyer request aur supplier offers save aur score ke mutabiq sort kiye ja rahe hain.
def boli_page():
    header(); st.header("💰 BARE BAZAR BOLI"); st.caption("Seedhi Boli, Seedha Rate")
    if helper(st.session_state.logged): st.markdown('<div class="alert">🚨 YE IZZAT CIRCLE MEMBER HAI. IZZAT SE BAAT KARO</div>',unsafe_allow_html=True)
    with st.form("boli_form"):
        p=st.text_input("Product Name"); qty=st.number_input("Quantity",min_value=1,step=1); b=st.selectbox("Bazaar",BAZAARS); bud=st.number_input("Budget (Rs.)",min_value=1.0,step=100.0); ok=st.form_submit_button("📢 Boli Request Post Karein")
    if ok:
        if not p.strip(): st.error("Product name required hai.")
        else: x("INSERT INTO boli_requests(buyer_phone,product_name,quantity,bazaar,budget,created_at) VALUES(?,?,?,?,?,?)",(st.session_state.logged,p.strip(),qty,b,bud,now()));st.success("✅ Boli Request Post ho gayi.");st.rerun()
    req=q("SELECT b.*,u.name buyer_name,u.izzat_points buyer_points FROM boli_requests b LEFT JOIN users u ON u.phone=b.buyer_phone ORDER BY b.id DESC")
    for _,r in req.iterrows():
        with st.container(border=True):
            st.markdown(f"### 🏪 {r.product_name} — {r.bazaar}"); st.write(f"Buyer: **{r.buyer_name}** • Qty: **{int(r.quantity)}** • Budget: **Rs. {r.budget:,.0f}**")
            if int(r.buyer_points or 0)>5: st.markdown('<div class="alert">🚨 YE IZZAT CIRCLE MEMBER HAI. IZZAT SE BAAT KARO</div>',unsafe_allow_html=True)
            u=user(st.session_state.logged)
            if u and u["user_type"]=="Supplier/Helper":
                with st.form(f"offer_{r.id}"):
                    rate=st.number_input("Aap ka Rate (Rs.)",min_value=1.0,step=10.0,key=f"rate{r.id}"); comment=st.text_input("Comment",key=f"comment{r.id}"); send=st.form_submit_button("💼 Offer Dein")
                if send: x("INSERT INTO offers(boli_request_id,seller_phone,rate,comment,created_at) VALUES(?,?,?,?,?)",(r.id,st.session_state.logged,rate,comment,now()));st.success("Offer save ho gayi.");st.rerun()
            offers=q("SELECT o.*,u.name seller_name,u.izzat_points FROM offers o LEFT JOIN users u ON u.phone=o.seller_phone WHERE o.boli_request_id=? ORDER BY u.izzat_points DESC,o.rate ASC",(r.id,))
            for _,o in offers.iterrows():
                a,c,d=st.columns([2,1,2]); a.write(f"**{o.seller_name}** ⭐ {int(o.izzat_points or 0)}"); c.write(f"Rs. {o.rate:,.0f}"); d.write(o.comment or "No comment")
                if r.buyer_phone==st.session_state.logged and st.button("🚩 Report",key=f"rep{o.id}"):
                    add_points(o.seller_phone,-5); x("UPDATE offers SET reported=1 WHERE id=?",(o.id,));st.warning("Seller report ho gaya aur 5 points cut ho gaye.");st.rerun()

# Urdu: Izzat Circle System current score aur rules display karta hai.
def system_page():
    header(); st.header("⭐ IZZAT CIRCLE SYSTEM"); u=user(st.session_state.logged); p=points(st.session_state.logged); a,b,c=st.columns(3); a.metric("Izzat Points",p); b.metric("Status","HELPER" if p>5 else "Aam Admi"); c.metric("Type",u["user_type"] if u else "-"); st.markdown("- ⭐ Izzat_Points > 5 = Helper\n- 🚨 Helper ko Boli mein red alert\n- 📊 Offers Izzat Score ke hisaab se priority\n- 🚩 Report par seller ke 5 points minus")

# Urdu: Unity page community stats aur bhaichara message show karta hai.
def unity_page():
    header(); st.header("🤲 UNITY / BHAICHARA"); st.subheader("Rat Ko Koi Bhuka Na Soye"); a,b,c=st.columns(3); a.metric("Help",q("SELECT COUNT(*) n FROM help_requests WHERE request_type='Help'").iloc[0].n); b.metric("Donation",q("SELECT COUNT(*) n FROM help_requests WHERE request_type='Donation'").iloc[0].n); c.metric("Heroes",q("SELECT COUNT(*) n FROM users WHERE izzat_points>5").iloc[0].n); st.success("🤝 Apne mohalla mein jis ko zaroorat ho, us tak izzat ke saath madad pohanchana hi IZZAT CIRCLE ka mission hai.")

# Urdu: COD shop ke demo products aur orders database mein save kiye ja rahe hain.
def shop():
    st.subheader("🛒 IZZAT CIRCLE Shop — COD")
    products=[("Kitchen Organizer",1299), ("LED Study Lamp",1499), ("Storage Box",999), ("Mobile Stand",599)]
    cs=st.columns(2)
    for i,(name,price) in enumerate(products):
        with cs[i%2]:
            with st.container(border=True):
                st.markdown(f"### 🛍️ {name}"); st.write(f"Rs. {price:,.0f}")
                with st.form(f"cod{i}"):
                    qty=st.number_input("Quantity",1,10,1,key=f"q{i}"); addr=st.text_input("Address",key=f"a{i}"); ok=st.form_submit_button("📦 Order COD")
                if ok:
                    if not addr.strip(): st.error("Address required hai.")
                    else: x("INSERT INTO orders(customer_phone,product_name,price,quantity,address,created_at) VALUES(?,?,?,?,?,?)",(st.session_state.logged,name,price,qty,addr,now()));st.success("COD order save ho gaya.")

# Urdu: Poster service order aur uploaded file ko uploads folder aur database mein save kiya ja raha hai.
def poster():
    st.subheader("🎨 Poster Design Service")
    with st.form("poster"):
        n=st.text_input("Name"); un=st.text_input("University"); typ=st.selectbox("Poster Type",["Business","Academic","Competition"]); details=st.text_area("Details"); f=st.file_uploader("File Upload",type=["png","jpg","jpeg","pdf","docx","pptx"]); ok=st.form_submit_button("Submit Poster Order")
    if ok:
        if not n.strip() or not un.strip() or not details.strip(): st.error("Name, University aur Details required hain.")
        else:
            path=""
            if f:
                path=os.path.join(UPLOADS,secrets.token_hex(5)+"_"+re.sub(r"[^a-zA-Z0-9_.-]","_",f.name));open(path,"wb").write(f.getbuffer())
            x("INSERT INTO poster_orders(phone,name,university,poster_type,details,file_path,created_at) VALUES(?,?,?,?,?,?,?)",(st.session_state.logged,n,un,typ,details,path,now()));st.success("Poster order save ho gaya.")

# Urdu: Portfolio mein teen projects show kiye ja rahe hain.
def portfolio():
    st.subheader("📁 Portfolio Showcase")
    for title,desc in [("MF Traders Poster","Business promotional poster design."),("IMechE UET Taxila AKDC Team Mistry Phantoms","Engineering team and competition project showcase."),("Student Research Posters","Academic/research poster layouts.")]:
        with st.container(border=True): st.markdown(f"### 🖼️ {title}");st.write(desc);st.caption("Project image yahan add ki ja sakti hai.")

# Urdu: Sidebar mein sirf requested IZZAT CIRCLE navigation rakhi ja rahi hai.
def sidebar():
    with st.sidebar:
        st.markdown("# 🤝 IZZAT CIRCLE");st.caption("Madad karo, Izzat pao");u=user(st.session_state.logged);st.success(f"👤 {u['name']}\n\n⭐ {int(u['izzat_points'])} Points") if u else None;st.divider()
        p=st.radio("Navigation",["Izzat Circle","Mohalla Help","Mohalla Bazar","Bare Bazar Boli","Izzat Circle System","Unity"])
        st.divider()
        if st.button("🚪 Logout",use_container_width=True): st.session_state.clear();st.rerun()
        return p

# Urdu: Main function login, profile aur page navigation ko control karti hai.
def main():
    init_db()
    if "logged" not in st.session_state: login(); return
    if not profile(): return
    p=sidebar()
    if p=="Izzat Circle":home()
    elif p=="Mohalla Help":help_page()
    elif p=="Mohalla Bazar":bazar_page()
    elif p=="Bare Bazar Boli":boli_page()
    elif p=="Izzat Circle System":system_page()
    elif p=="Unity":unity_page()

# Urdu: Program direct run hone par main app start ki ja rahi hai.
if __name__=="__main__": main()
