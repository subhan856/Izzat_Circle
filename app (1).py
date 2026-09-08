import os
import sqlite3
import uuid
from datetime import datetime

import pandas as pd
import streamlit as st
import folium
from geopy.distance import geodesic
from streamlit_folium import st_folium


# Urdu: App ki basic configuration yahan set ki ja rahi hai.
st.set_page_config(
    page_title="GharBazar.pk",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_FILE = "gharbazar.db"
UPLOAD_DIR = "uploads"

# Urdu: Upload folder agar na ho to create kiya ja raha hai.
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Urdu: Demo suppliers ke liye Rawalpindi aur Islamabad ki locations define ki ja rahi hain.
DEMO_SUPPLIERS = [
    ("SUP-001", "Rawalpindi Wholesale Hub", "0300-1111111", 33.6007, 73.0679, "Rawalpindi"),
    ("SUP-002", "Raja Bazar Supplier", "0301-2222222", 33.6240, 73.0660, "Rawalpindi"),
    ("SUP-003", "Islamabad Trade Point", "0302-3333333", 33.6844, 73.0479, "Islamabad"),
    ("SUP-004", "Blue Area Supplier", "0303-4444444", 33.7077, 73.0498, "Islamabad"),
    ("SUP-005", "I-10 Supplier Center", "0304-5555555", 33.6581, 73.0124, "Islamabad"),
]


# Urdu: App ka green aur golden mobile-friendly theme apply kiya ja raha hai.
st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(180deg,#f7fff9 0%,#ffffff 100%); }
    .brand { text-align:center; color:#075e32; font-size:44px; font-weight:900; letter-spacing:1px; }
    .tagline { text-align:center; color:#b8860b; font-size:18px; font-weight:700; }
    .mission { background:linear-gradient(90deg,#075e32,#0b7a43); color:white;
               padding:14px; border-radius:15px; text-align:center; font-weight:800; }
    .card { background:white; border:1px solid #d4af37; border-radius:16px; padding:18px;
            box-shadow:0 3px 12px rgba(0,0,0,.07); margin-bottom:12px; }
    .gold-card { background:#fff9df; border:2px solid #d4af37; border-radius:14px; padding:16px; }
    .alert-member { background:#ffe5e5; border:2px solid #d60000; color:#a00000;
                    padding:15px; border-radius:12px; font-weight:800; }
    .hero { background:linear-gradient(135deg,#075e32,#0b7a43); color:white;
            padding:16px; border-radius:14px; margin-bottom:10px; }
    div.stButton > button { width:100%; border-radius:11px; font-weight:700; }
    @media(max-width:768px){ .brand{font-size:31px;} .tagline{font-size:15px;} }
    </style>
    """,
    unsafe_allow_html=True,
)


# Urdu: SQLite database ka connection safely open kiya ja raha hai.
def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# Urdu: Orders, poster orders aur suppliers ki teen required tables create ki ja rahi hain.
def init_database():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE NOT NULL,
            product_name TEXT NOT NULL,
            price REAL NOT NULL,
            customer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            payment_method TEXT NOT NULL DEFAULT 'Cash on Delivery',
            status TEXT NOT NULL DEFAULT 'New',
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS poster_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            poster_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            university TEXT NOT NULL,
            poster_type TEXT NOT NULL,
            details TEXT NOT NULL,
            file_name TEXT,
            file_path TEXT,
            status TEXT NOT NULL DEFAULT 'New',
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            area TEXT NOT NULL
        )
    """)

    for row in DEMO_SUPPLIERS:
        cur.execute("""
            INSERT OR IGNORE INTO suppliers
            (supplier_id,name,phone,latitude,longitude,area)
            VALUES (?,?,?,?,?,?)
        """, row)

    conn.commit()
    conn.close()


# Urdu: Naya Cash on Delivery order SQLite database mein save kiya ja raha hai.
def save_order(product_name, price, customer_name, phone, address, quantity):
    order_id = "ORD-" + uuid.uuid4().hex[:8].upper()

    conn = get_db()
    conn.execute("""
        INSERT INTO orders
        (order_id,product_name,price,customer_name,phone,address,quantity,
         payment_method,status,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (
        order_id,
        product_name,
        price,
        customer_name,
        phone,
        address,
        quantity,
        "Cash on Delivery",
        "New",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    ))

    conn.commit()
    conn.close()

    return order_id


# Urdu: Poster order aur uploaded file ko database aur uploads folder mein save kiya ja raha hai.
def save_poster_order(name, university, poster_type, details, uploaded_file):
    poster_id = "POST-" + uuid.uuid4().hex[:8].upper()

    file_name = ""
    file_path = ""

    if uploaded_file is not None:
        safe_name = os.path.basename(uploaded_file.name).replace(" ", "_")
        file_name = safe_name
        file_path = os.path.join(
            UPLOAD_DIR,
            poster_id + "_" + safe_name
        )

        with open(file_path, "wb") as file:
            file.write(uploaded_file.getbuffer())

    conn = get_db()
    conn.execute("""
        INSERT INTO poster_orders
        (poster_id,name,university,poster_type,details,file_name,file_path,
         status,created_at)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (
        poster_id,
        name,
        university,
        poster_type,
        details,
        file_name,
        file_path,
        "New",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    ))

    conn.commit()
    conn.close()

    return poster_id


# Urdu: Saare COD orders database se read kiye ja rahe hain.
def load_orders():
    conn = get_db()
    df = pd.read_sql_query(
        "SELECT * FROM orders ORDER BY id DESC",
        conn
    )
    conn.close()
    return df


# Urdu: Saare poster orders database se read kiye ja rahe hain.
def load_poster_orders():
    conn = get_db()
    df = pd.read_sql_query(
        "SELECT * FROM poster_orders ORDER BY id DESC",
        conn
    )
    conn.close()
    return df


# Urdu: Supplier records database se read kiye ja rahe hain.
def load_suppliers():
    conn = get_db()
    df = pd.read_sql_query(
        "SELECT * FROM suppliers ORDER BY id",
        conn
    )
    conn.close()
    return df


# Urdu: COD order ko Sent to Supplier status diya ja raha hai.
def mark_order_sent(order_id):
    conn = get_db()
    conn.execute(
        "UPDATE orders SET status='Sent to Supplier' WHERE order_id=?",
        (order_id,)
    )
    conn.commit()
    conn.close()


# Urdu: Poster order ka status admin ke zariye update kiya ja raha hai.
def mark_poster_status(poster_id, status):
    conn = get_db()
    conn.execute(
        "UPDATE poster_orders SET status=? WHERE poster_id=?",
        (status, poster_id)
    )
    conn.commit()
    conn.close()


# Urdu: Purane Izzat Circle CSV files ko preserve karke initialize kiya ja raha hai.
def initialize_legacy_csv_files():
    schemas = {
        "users.csv": [
            "User_ID", "Name", "Phone", "Izzat_Points", "Created_At"
        ],
        "help_requests.csv": [
            "Request_ID", "Name", "Phone", "Problem", "Latitude",
            "Longitude", "Senior_Citizen", "Senior_Remarks", "Status",
            "Izzat_Star", "Helper_Phone", "Created_At"
        ],
        "products.csv": [
            "Product_ID", "Dukan_Naam", "Product", "Price", "Image_URL",
            "Phone", "Latitude", "Longitude", "Created_At"
        ],
        "wholesale_requests.csv": [
            "Request_ID", "Buyer_Name", "Buyer_Phone", "Bazar",
            "Product_Naam", "Quantity", "Budget", "Created_At"
        ],
        "offers.csv": [
            "Offer_ID", "Request_ID", "Seller_Name", "Seller_Phone",
            "Rate", "Comment", "Reported", "Report_Reason", "Created_At"
        ],
    }

    for filename, columns in schemas.items():
        if not os.path.exists(filename):
            pd.DataFrame(columns=columns).to_csv(
                filename,
                index=False,
                encoding="utf-8-sig"
            )


# Urdu: Legacy CSV file ko safely DataFrame mein load kiya ja raha hai.
def load_csv(filename):
    try:
        return pd.read_csv(
            filename,
            encoding="utf-8-sig"
        )
    except Exception:
        return pd.DataFrame()


# Urdu: Legacy DataFrame ko CSV file mein save kiya ja raha hai.
def save_csv(df, filename):
    df.to_csv(
        filename,
        index=False,
        encoding="utf-8-sig"
    )


# Urdu: User ko Izzat Circle users.csv mein create ya update kiya ja raha hai.
def create_or_update_user(name, phone):
    users = load_csv("users.csv")

    if users.empty:
        users = pd.DataFrame(columns=[
            "User_ID",
            "Name",
            "Phone",
            "Izzat_Points",
            "Created_At"
        ])

    phone = str(phone).strip()

    mask = users["Phone"].astype(str).str.strip() == phone

    if not mask.any():
        users = pd.concat(
            [
                users,
                pd.DataFrame([{
                    "User_ID": "USR-" + uuid.uuid4().hex[:8].upper(),
                    "Name": name,
                    "Phone": phone,
                    "Izzat_Points": 0,
                    "Created_At": datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                }])
            ],
            ignore_index=True
        )
    else:
        users.loc[mask, "Name"] = name

    save_csv(users, "users.csv")


# Urdu: Phone number se Izzat Points read kiye ja rahe hain.
def get_user_points(phone):
    users = load_csv("users.csv")

    if users.empty:
        return 0

    result = users[
        users["Phone"].astype(str).str.strip()
        == str(phone).strip()
    ]

    if result.empty:
        return 0

    try:
        return int(float(result.iloc[0]["Izzat_Points"]))
    except Exception:
        return 0


# Urdu: User ke Izzat Points mein points add ya minus kiye ja rahe hain.
def change_user_points(phone, points):
    users = load_csv("users.csv")

    if users.empty:
        return False

    mask = users["Phone"].astype(str).str.strip() == str(phone).strip()

    if not mask.any():
        return False

    idx = users[mask].index[0]

    try:
        old_points = int(float(users.at[idx, "Izzat_Points"]))
    except Exception:
        old_points = 0

    users.at[idx, "Izzat_Points"] = max(
        0,
        old_points + int(points)
    )

    save_csv(users, "users.csv")
    return True


# Urdu: Check kiya ja raha hai ke user Izzat Circle Helper hai ya nahi.
def is_helper(phone):
    return get_user_points(phone) > 5


# Urdu: Do map locations ke darmiyan distance calculate kiya ja raha hai.
def calculate_distance_km(lat1, lon1, lat2, lon2):
    try:
        return geodesic(
            (float(lat1), float(lon1)),
            (float(lat2), float(lon2))
        ).km
    except Exception:
        return 999999


# Urdu: Existing Folium map ko preserve karke map par click location li ja rahi hai.
def location_picker(key, default_lat=33.6844, default_lon=73.0479):
    st.caption("📍 Map par click karke location select karein.")

    map_object = folium.Map(
        location=[default_lat, default_lon],
        zoom_start=13,
        control_scale=True
    )

    folium.Marker(
        [default_lat, default_lon],
        popup="Default Location"
    ).add_to(map_object)

    map_data = st_folium(
        map_object,
        width=None,
        height=350,
        key=key
    )

    if map_data and map_data.get("last_clicked"):
        clicked = map_data["last_clicked"]
        return clicked.get("lat"), clicked.get("lng")

    return None, None


# Urdu: Five dummy suppliers ke markers aur click par unki details map mein dikhayi ja rahi hain.
def supplier_map():
    suppliers = load_suppliers()

    if suppliers.empty:
        st.info("Supplier data available nahi.")
        return

    map_object = folium.Map(
        location=[33.6844, 73.0479],
        zoom_start=11,
        control_scale=True
    )

    for _, row in suppliers.iterrows():
        popup_html = (
            f"<b>{row['name']}</b><br>"
            f"📞 {row['phone']}<br>"
            f"📍 {row['area']}<br>"
            f"Supplier ID: {row['supplier_id']}"
        )

        folium.Marker(
            [row["latitude"], row["longitude"]],
            popup=folium.Popup(
                popup_html,
                max_width=280
            ),
            tooltip=f"{row['name']} — {row['area']}",
            icon=folium.Icon(
                color="green",
                icon="shopping-cart"
            )
        ).add_to(map_object)

    st_folium(
        map_object,
        width=None,
        height=500,
        key="supplier_map"
    )


# Urdu: User ki location ke qareeb suppliers radius ke andar filter kiye ja rahe hain.
def nearby_suppliers(lat, lon, radius_km=10):
    suppliers = load_suppliers()

    if suppliers.empty:
        return suppliers

    suppliers["Distance_KM"] = suppliers.apply(
        lambda row: round(
            calculate_distance_km(
                lat,
                lon,
                row["latitude"],
                row["longitude"]
            ),
            2
        ),
        axis=1
    )

    return suppliers[
        suppliers["Distance_KM"] <= radius_km
    ].sort_values("Distance_KM")


# Urdu: Home page par GharBazar.pk ka brand aur business concepts dikhaye ja rahe hain.
def home_page():
    st.markdown(
        '<div class="brand">🛍️ GharBazar.pk</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="tagline">Apno Se Khareedo • Seedha Rate • COD</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="mission">Pehle Izzat, Phir Deal</div>',
        unsafe_allow_html=True
    )

    st.write("")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            """
            <div class="card">
            <h3>🛒 Dropshipping Store</h3>
            <p>Product dekhein aur Cash on Delivery order karein.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            """
            <div class="card">
            <h3>🎨 Poster Design Service</h3>
            <p>Business, Academic aur Competition posters order karein.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c3:
        st.markdown(
            """
            <div class="card">
            <h3>📍 Supplier Near Me</h3>
            <p>Rawalpindi/Islamabad suppliers map par dekhein.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.subheader("⭐ Existing Izzat Circle")

    st.caption(
        "Purane Mohalla Help, Mohalla Bazar aur Bare Bazar Boli "
        "CSV workflows preserve kiye gaye hain."
    )

    users = load_csv("users.csv")

    if not users.empty:
        users["Izzat_Points"] = pd.to_numeric(
            users["Izzat_Points"],
            errors="coerce"
        ).fillna(0)

        heroes = users[
            users["Izzat_Points"] > 5
        ].sort_values(
            "Izzat_Points",
            ascending=False
        ).head(5)

        for rank, (_, user) in enumerate(
            heroes.iterrows(),
            start=1
        ):
            st.markdown(
                f"""
                <div class="hero">
                #{rank} 🤝 {user["Name"]}
                — ⭐ {int(user["Izzat_Points"])} Izzat Points
                </div>
                """,
                unsafe_allow_html=True
            )


# Urdu: Demo dropshipping products ka responsive grid display kiya ja raha hai.
def shop_page():
    st.title("🛒 GharBazar.pk Store")
    st.caption("Dropshipping Store — Order COD")

    products = [
        {
            "name": "Premium Wireless Earbuds",
            "price": 2499,
            "image": "https://images.unsplash.com/photo-1606220945770-b5b6c2c55bf1?auto=format&fit=crop&w=800&q=80"
        },
        {
            "name": "Smart Watch",
            "price": 3499,
            "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=800&q=80"
        },
        {
            "name": "Portable Mini Speaker",
            "price": 1999,
            "image": "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?auto=format&fit=crop&w=800&q=80"
        },
        {
            "name": "Laptop Backpack",
            "price": 2799,
            "image": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=800&q=80"
        },
        {
            "name": "LED Desk Lamp",
            "price": 1599,
            "image": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=800&q=80"
        },
        {
            "name": "Phone Stand",
            "price": 899,
            "image": "https://images.unsplash.com/photo-1586953208448-b95a79798f07?auto=format&fit=crop&w=800&q=80"
        },
    ]

    for start in range(0, len(products), 3):
        cols = st.columns(3)

        for col, product in zip(
            cols,
            products[start:start + 3]
        ):
            with col:
                st.markdown(
                    '<div class="card">',
                    unsafe_allow_html=True
                )

                st.image(
                    product["image"],
                    use_container_width=True
                )

                st.subheader(product["name"])

                st.markdown(
                    f"### Rs. {product['price']:,}"
                )

                if st.button(
                    "🛍️ Order COD",
                    key="buy_" + product["name"]
                ):
                    st.session_state[
                        "selected_product"
                    ] = product

                    st.session_state[
                        "page_override"
                    ] = "checkout"

                    st.rerun()

                st.markdown(
                    "</div>",
                    unsafe_allow_html=True
                )


# Urdu: Selected product ka COD checkout form aur order save kiya ja raha hai.
def checkout_page():
    product = st.session_state.get("selected_product")

    if not product:
        st.warning("Pehle product select karein.")
        return

    st.title("📦 COD Order")

    st.info(
        f"{product['name']} — Rs. {product['price']:,}"
    )

    with st.form("cod_form"):
        name = st.text_input("Customer Name")
        phone = st.text_input("Phone Number")
        address = st.text_area("Complete Delivery Address")
        quantity = st.number_input(
            "Quantity",
            min_value=1,
            max_value=20,
            value=1,
            step=1
        )

        submit = st.form_submit_button(
            "✅ Place COD Order"
        )

    if submit:
        if (
            not name.strip()
            or not phone.strip()
            or not address.strip()
        ):
            st.error(
                "Name, phone aur complete address required hain."
            )
        else:
            order_id = save_order(
                product["name"],
                float(product["price"]),
                name.strip(),
                phone.strip(),
                address.strip(),
                int(quantity)
            )

            st.success(
                f"🎉 Order placed successfully! Order ID: {order_id}"
            )

            st.session_state.pop(
                "selected_product",
                None
            )


# Urdu: Poster Design Service ka form aur file upload handle kiya ja raha hai.
def poster_page():
    st.title("🎨 Poster Design Service")
    st.caption("Business • Academic • Competition")

    with st.form("poster_form"):
        name = st.text_input("Name")
        university = st.text_input("University")

        poster_type = st.selectbox(
            "Poster Type",
            [
                "Business",
                "Academic",
                "Competition"
            ]
        )

        details = st.text_area(
            "Details / Requirements"
        )

        uploaded_file = st.file_uploader(
            "File Upload — Optional",
            type=[
                "png",
                "jpg",
                "jpeg",
                "pdf",
                "docx",
                "pptx"
            ]
        )

        submit = st.form_submit_button(
            "📤 Submit Poster Order"
        )

    if submit:
        if (
            not name.strip()
            or not university.strip()
            or not details.strip()
        ):
            st.error(
                "Name, University aur Details required hain."
            )
        else:
            poster_id = save_poster_order(
                name.strip(),
                university.strip(),
                poster_type,
                details.strip(),
                uploaded_file
            )

            st.success(
                f"🎨 Poster order received! ID: {poster_id}"
            )


# Urdu: Portfolio ke teen projects image aur description ke sath display kiye ja rahe hain.
def portfolio_page():
    st.title("📁 Portfolio Showcase")

    projects = [
        (
            "MF Traders Poster",
            "Business branding aur promotional poster concept with clean commercial layout.",
            "https://images.unsplash.com/photo-1558655146-d09347e92766?auto=format&fit=crop&w=1000&q=80"
        ),
        (
            "IMechE UET Taxila AKDC Team Mistry Phantoms",
            "Engineering competition identity aur submarine project presentation work.",
            "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1000&q=80"
        ),
        (
            "Student Research Posters",
            "Academic research posters designed for clear data presentation and university submissions.",
            "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1000&q=80"
        ),
    ]

    for name, description, image in projects:
        c1, c2 = st.columns([1, 1])

        with c1:
            st.image(
                image,
                use_container_width=True
            )

        with c2:
            st.markdown(f"### {name}")
            st.write(description)
            st.markdown(
                "**Service focus:** clean layout • readable typography • presentation-ready design"
            )

        st.divider()


# Urdu: Admin page par orders, poster requests, status controls aur CSV export display kiye ja rahe hain.
def admin_page():
    st.title("🔐 Supplier Panel / Admin")

    st.warning(
        "Demo admin panel hai. Production deployment mein authentication zaroor add karein."
    )

    orders = load_orders()
    posters = load_poster_orders()

    st.subheader("📦 All COD Orders")

    if orders.empty:
        st.info("Abhi koi COD order nahi.")
    else:
        for _, row in orders.iterrows():
            with st.expander(
                f"{row['order_id']} — {row['product_name']} — {row['status']}"
            ):
                st.write(
                    f"**Customer:** {row['customer_name']}"
                )
                st.write(
                    f"**Phone:** {row['phone']}"
                )
                st.write(
                    f"**Address:** {row['address']}"
                )
                st.write(
                    f"**Quantity:** {row['quantity']}"
                )
                st.write(
                    f"**Total:** Rs. {row['price'] * row['quantity']:,.0f}"
                )
                st.write(
                    f"**Created:** {row['created_at']}"
                )

                if row["status"] != "Sent to Supplier":
                    if st.button(
                        "🚚 Mark as Sent to Supplier",
                        key="sent_" + row["order_id"]
                    ):
                        mark_order_sent(
                            row["order_id"]
                        )
                        st.success(
                            "Order supplier ko send mark kar diya gaya."
                        )
                        st.rerun()

        st.download_button(
            "⬇️ Export Orders to CSV",
            data=orders.to_csv(
                index=False
            ).encode("utf-8-sig"),
            file_name="orders_export.csv",
            mime="text/csv",
        )

    st.divider()

    st.subheader("🎨 Poster Orders")

    if posters.empty:
        st.info("Abhi koi poster order nahi.")
    else:
        for _, row in posters.iterrows():
            with st.expander(
                f"{row['poster_id']} — {row['name']} — {row['status']}"
            ):
                st.write(
                    f"**University:** {row['university']}"
                )
                st.write(
                    f"**Type:** {row['poster_type']}"
                )
                st.write(
                    f"**Details:** {row['details']}"
                )
                st.write(
                    f"**File:** {row['file_name'] or 'No file uploaded'}"
                )

                if (
                    row["file_path"]
                    and os.path.exists(row["file_path"])
                ):
                    with open(
                        row["file_path"],
                        "rb"
                    ) as file:
                        st.download_button(
                            "⬇️ Download Uploaded File",
                            data=file.read(),
                            file_name=row["file_name"],
                            key="download_" + row["poster_id"]
                        )

                statuses = [
                    "New",
                    "In Progress",
                    "Completed"
                ]

                current_status = (
                    row["status"]
                    if row["status"] in statuses
                    else "New"
                )

                new_status = st.selectbox(
                    "Status",
                    statuses,
                    index=statuses.index(
                        current_status
                    ),
                    key="status_" + row["poster_id"]
                )

                if st.button(
                    "💾 Update Status",
                    key="update_" + row["poster_id"]
                ):
                    mark_poster_status(
                        row["poster_id"],
                        new_status
                    )
                    st.success("Status updated.")
                    st.rerun()

        st.download_button(
            "⬇️ Export Poster Orders to CSV",
            data=posters.to_csv(
                index=False
            ).encode("utf-8-sig"),
            file_name="poster_orders_export.csv",
            mime="text/csv",
        )

    st.divider()

    st.subheader("📊 Quick Stats")

    a, b, c = st.columns(3)

    a.metric(
        "COD Orders",
        len(orders)
    )

    b.metric(
        "Poster Orders",
        len(posters)
    )

    c.metric(
        "Suppliers",
        len(load_suppliers())
    )


# Urdu: Supplier map aur Find Supplier Near Me search dono yahan display kiye ja rahe hain.
def map_page():
    st.title("📍 Find Supplier Near Me")
    st.caption(
        "Rawalpindi / Islamabad Supplier Network"
    )

    st.info(
        "Map par supplier marker click karein; popup mein name, phone aur area nazar aayega."
    )

    supplier_map()

    st.subheader(
        "📌 Search Suppliers Near Your Location"
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        lat = st.number_input(
            "Your Latitude",
            value=33.6844,
            format="%.6f"
        )

    with c2:
        lon = st.number_input(
            "Your Longitude",
            value=73.0479,
            format="%.6f"
        )

    with c3:
        radius = st.number_input(
            "Radius (KM)",
            min_value=1.0,
            max_value=50.0,
            value=10.0,
            step=1.0
        )

    if st.button(
        "🔎 Find Supplier Near Me"
    ):
        result = nearby_suppliers(
            lat,
            lon,
            radius
        )

        if result.empty:
            st.warning(
                "Is radius mein supplier nahi mila."
            )
        else:
            st.success(
                f"{len(result)} supplier(s) mile."
            )

            st.dataframe(
                result[
                    [
                        "name",
                        "phone",
                        "area",
                        "Distance_KM"
                    ]
                ].rename(
                    columns={
                        "name": "Supplier",
                        "phone": "Phone",
                        "area": "Area",
                        "Distance_KM": "Distance (KM)"
                    }
                ),
                use_container_width=True,
                hide_index=True
            )


# Urdu: Existing Mohalla Help ka basic data-entry workflow preserve kiya ja raha hai.
def mohalla_help_page():
    st.title("🤝 Mohalla Help")
    st.caption("Ek Dosre Kaam Aao")

    lat, lon = location_picker(
        "help_location_map"
    )

    with st.form("help_form"):
        name = st.text_input("Naam")
        phone = st.text_input("Phone")
        problem = st.text_area("Problem")
        senior = st.checkbox(
            "👴 Senior Citizen Request"
        )
        remarks = st.text_area(
            "Senior Citizen Remarks"
        )

        submit = st.form_submit_button(
            "📤 Help Request Submit"
        )

    if submit:
        if (
            not name
            or not phone
            or not problem
            or lat is None
        ):
            st.error(
                "Naam, phone, problem aur map location required hain."
            )
        else:
            create_or_update_user(
                name,
                phone
            )

            df = load_csv(
                "help_requests.csv"
            )

            new_row = {
                "Request_ID": "HELP-" + uuid.uuid4().hex[:8].upper(),
                "Name": name,
                "Phone": phone,
                "Problem": problem,
                "Latitude": lat,
                "Longitude": lon,
                "Senior_Citizen": "Yes" if senior else "No",
                "Senior_Remarks": remarks,
                "Status": "Open",
                "Izzat_Star": "",
                "Helper_Phone": "",
                "Created_At": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            }

            df = pd.concat(
                [
                    df,
                    pd.DataFrame([new_row])
                ],
                ignore_index=True
            )

            save_csv(
                df,
                "help_requests.csv"
            )

            st.success(
                "Help request save ho gayi."
            )


# Urdu: Existing Mohalla Bazar ka product-entry workflow preserve kiya ja raha hai.
def mohalla_bazar_page():
    st.title("🛒 Mohalla Bazar")
    st.caption("Apno Se Khareedo")

    st.subheader("➕ Product Add")

    lat, lon = location_picker(
        "seller_location_map"
    )

    with st.form("product_form"):
        shop = st.text_input("Dukan Naam")
        product = st.text_input("Product")
        price = st.number_input(
            "Price Rs.",
            min_value=0.0,
            step=10.0
        )
        image_url = st.text_input(
            "Image URL"
        )
        phone = st.text_input(
            "Phone"
        )

        submit = st.form_submit_button(
            "🛍️ Add Product"
        )

    if submit:
        if (
            not shop
            or not product
            or not phone
            or lat is None
        ):
            st.error(
                "Dukan, product, phone aur location required hain."
            )
        else:
            create_or_update_user(
                shop,
                phone
            )

            df = load_csv(
                "products.csv"
            )

            new_row = {
                "Product_ID": "PROD-" + uuid.uuid4().hex[:8].upper(),
                "Dukan_Naam": shop,
                "Product": product,
                "Price": price,
                "Image_URL": image_url,
                "Phone": phone,
                "Latitude": lat,
                "Longitude": lon,
                "Created_At": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            }

            df = pd.concat(
                [
                    df,
                    pd.DataFrame([new_row])
                ],
                ignore_index=True
            )

            save_csv(
                df,
                "products.csv"
            )

            st.success(
                "Product add ho gaya."
            )


# Urdu: Existing Bare Bazar Boli ki CSV requests ko preserve karke display kiya ja raha hai.
def bare_bazar_boli_page():
    st.title("🏪 Bare Bazar Boli")
    st.caption("Seedhi Boli, Seedha Rate")

    st.info(
        "Legacy wholesale CSV workflow preserved hai. "
        "New GharBazar COD aur Poster workflows SQLite par hain."
    )

    df = load_csv(
        "wholesale_requests.csv"
    )

    if df.empty:
        st.info(
            "Abhi koi wholesale request nahi."
        )
    else:
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )


# Urdu: Sidebar navigation, admin query parameter aur page routing yahan handle ki ja rahi hai.
def main():
    init_database()
    initialize_legacy_csv_files()

    pages = [
        "Home",
        "Shop",
        "Order Poster",
        "Portfolio",
        "Admin",
        "Map",
        "Mohalla Help",
        "Mohalla Bazar",
        "Bare Bazar Boli",
    ]

    page_map = {
        "home": "Home",
        "shop": "Shop",
        "poster": "Order Poster",
        "portfolio": "Portfolio",
        "admin": "Admin",
        "map": "Map",
        "help": "Mohalla Help",
        "bazar": "Mohalla Bazar",
        "wholesale": "Bare Bazar Boli",
    }

    query_page = st.query_params.get("page")

    default_page = (
        page_map.get(
            str(query_page).lower(),
            "Home"
        )
        if query_page
        else "Home"
    )

    if "page_override" in st.session_state:
        default_page = st.session_state.pop(
            "page_override"
        )

    with st.sidebar:
        st.markdown("## 🛍️ GharBazar.pk")

        selected = st.radio(
            "Navigation",
            pages,
            index=pages.index(default_page)
        )

        st.divider()
        st.caption("Pehle Izzat, Phir Deal")
        st.caption("COD • Poster Design • Suppliers")

    if selected == "Home":
        home_page()

    elif selected == "Shop":
        shop_page()

    elif selected == "Order Poster":
        poster_page()

    elif selected == "Portfolio":
        portfolio_page()

    elif selected == "Admin":
        admin_page()

    elif selected == "Map":
        map_page()

    elif selected == "Mohalla Help":
        mohalla_help_page()

    elif selected == "Mohalla Bazar":
        mohalla_bazar_page()

    elif selected == "Bare Bazar Boli":
        bare_bazar_boli_page()

    elif selected == "Checkout":
        checkout_page()


# Urdu: Program ko start kiya ja raha hai.
if __name__ == "__main__":
    main()
