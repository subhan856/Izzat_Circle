# ============================================================
# IZZAT CIRCLE
# Slogan: "Madad karo, Izzat pao"
# Single-file Streamlit Web App
# ============================================================

import os
import uuid
from datetime import datetime

import pandas as pd
import streamlit as st
import folium

from geopy.distance import geodesic
from streamlit_folium import st_folium


# ============================================================
# Urdu: App ki basic configuration yahan set ki ja rahi hai.
# ============================================================
st.set_page_config(
    page_title="IZZAT CIRCLE",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# Urdu: App ka green aur golden theme CSS ke zariye banaya ja raha hai.
# ============================================================
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #f7fff9 0%, #ffffff 100%);
    }

    .main-title {
        text-align: center;
        color: #075e32;
        font-size: 46px;
        font-weight: 900;
        letter-spacing: 2px;
        margin-bottom: 0;
    }

    .slogan {
        text-align: center;
        color: #b8860b;
        font-size: 20px;
        font-weight: 700;
        margin-top: 2px;
    }

    .mission {
        text-align: center;
        background: linear-gradient(90deg, #075e32, #0b7a43);
        color: white;
        padding: 14px;
        border-radius: 15px;
        font-size: 20px;
        font-weight: bold;
        margin: 20px 0;
    }

    .concept-card {
        background: white;
        border: 2px solid #d4af37;
        border-radius: 18px;
        padding: 22px;
        text-align: center;
        min-height: 150px;
        box-shadow: 0 3px 12px rgba(0,0,0,0.08);
    }

    .concept-title {
        color: #075e32;
        font-size: 22px;
        font-weight: 800;
    }

    .concept-sub {
        color: #555;
        font-size: 16px;
        margin-top: 8px;
    }

    .hero-card {
        background: linear-gradient(135deg, #075e32, #0b7a43);
        color: white;
        padding: 18px;
        border-radius: 15px;
        margin-bottom: 10px;
    }

    .alert-member {
        background: #ffe5e5;
        border: 2px solid #d60000;
        color: #a00000;
        padding: 15px;
        border-radius: 12px;
        font-weight: bold;
        margin: 12px 0;
    }

    .gold-card {
        background: #fff9df;
        border: 2px solid #d4af37;
        padding: 15px;
        border-radius: 12px;
    }

    div.stButton > button {
        width: 100%;
        border-radius: 12px;
        font-weight: 700;
    }

    .small-text {
        color: #666;
        font-size: 13px;
    }

    @media (max-width: 768px) {
        .main-title {
            font-size: 32px;
        }

        .slogan {
            font-size: 17px;
        }

        .mission {
            font-size: 16px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# Urdu: CSV files ke naam aur unke columns define kiye ja rahe hain.
# ============================================================
FILES = {
    "users": "users.csv",
    "help": "help_requests.csv",
    "products": "products.csv",
    "wholesale": "wholesale_requests.csv",
    "offers": "offers.csv"
}


# ============================================================
# Urdu: Zaroori CSV files agar mojood na hon to automatically create hoti hain.
# ============================================================
def initialize_csv_files():
    schemas = {
        "users": [
            "User_ID",
            "Name",
            "Phone",
            "Izzat_Points",
            "Created_At"
        ],
        "help": [
            "Request_ID",
            "Name",
            "Phone",
            "Problem",
            "Latitude",
            "Longitude",
            "Senior_Citizen",
            "Senior_Remarks",
            "Status",
            "Izzat_Star",
            "Helper_Phone",
            "Created_At"
        ],
        "products": [
            "Product_ID",
            "Dukan_Naam",
            "Product",
            "Price",
            "Image_URL",
            "Phone",
            "Latitude",
            "Longitude",
            "Created_At"
        ],
        "wholesale": [
            "Request_ID",
            "Buyer_Name",
            "Buyer_Phone",
            "Bazar",
            "Product_Naam",
            "Quantity",
            "Budget",
            "Created_At"
        ],
        "offers": [
            "Offer_ID",
            "Request_ID",
            "Seller_Name",
            "Seller_Phone",
            "Rate",
            "Comment",
            "Reported",
            "Report_Reason",
            "Created_At"
        ]
    }

    for key, columns in schemas.items():
        if not os.path.exists(FILES[key]):
            pd.DataFrame(columns=columns).to_csv(
                FILES[key],
                index=False,
                encoding="utf-8-sig"
            )


# ============================================================
# Urdu: CSV file ko safely DataFrame mein load kiya ja raha hai.
# ============================================================
def load_csv(name):
    try:
        return pd.read_csv(FILES[name], encoding="utf-8-sig")
    except Exception:
        return pd.DataFrame()


# ============================================================
# Urdu: DataFrame ko CSV file mein save kiya ja raha hai.
# ============================================================
def save_csv(df, name):
    df.to_csv(
        FILES[name],
        index=False,
        encoding="utf-8-sig"
    )


# ============================================================
# Urdu: Unique ID generate karne ke liye ye function use hota hai.
# ============================================================
def make_id(prefix):
    return prefix + "_" + uuid.uuid4().hex[:8].upper()


# ============================================================
# Urdu: User ko users.csv mein create ya update kiya ja raha hai.
# ============================================================
def create_or_update_user(name, phone):
    users = load_csv("users")

    if users.empty:
        users = pd.DataFrame(columns=[
            "User_ID",
            "Name",
            "Phone",
            "Izzat_Points",
            "Created_At"
        ])

    phone = str(phone).strip()

    existing = users[
        users["Phone"].astype(str).str.strip() == phone
    ]

    if existing.empty:
        new_user = {
            "User_ID": make_id("USR"),
            "Name": name,
            "Phone": phone,
            "Izzat_Points": 0,
            "Created_At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        users = pd.concat(
            [users, pd.DataFrame([new_user])],
            ignore_index=True
        )
        save_csv(users, "users")
    else:
        idx = existing.index[0]
        users.at[idx, "Name"] = name
        save_csv(users, "users")


# ============================================================
# Urdu: Phone number se user ke Izzat Points hasil kiye ja rahe hain.
# ============================================================
def get_user_points(phone):
    users = load_csv("users")

    if users.empty:
        return 0

    result = users[
        users["Phone"].astype(str).str.strip() == str(phone).strip()
    ]

    if result.empty:
        return 0

    try:
        return int(float(result.iloc[0]["Izzat_Points"]))
    except Exception:
        return 0


# ============================================================
# Urdu: User ke Izzat Points mein points add ya minus kiye ja rahe hain.
# ============================================================
def change_user_points(phone, points):
    users = load_csv("users")

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

    new_points = max(0, old_points + int(points))

    users.at[idx, "Izzat_Points"] = new_points

    save_csv(users, "users")

    return True


# ============================================================
# Urdu: Check kiya ja raha hai ke user Izzat Circle Helper hai ya nahi.
# ============================================================
def is_helper(phone):
    return get_user_points(phone) > 5


# ============================================================
# Urdu: Latitude aur Longitude se do locations ke darmiyan distance nikala ja raha hai.
# ============================================================
def calculate_distance_km(lat1, lon1, lat2, lon2):
    try:
        return geodesic(
            (float(lat1), float(lon1)),
            (float(lat2), float(lon2))
        ).km
    except Exception:
        return 999999


# ============================================================
# Urdu: Map banaya ja raha hai jahan user click karke location select kar sakta hai.
# ============================================================
def location_picker(key, default_lat=33.6844, default_lon=73.0479):
    st.caption("📍 Map par click karke location select karein.")

    m = folium.Map(
        location=[default_lat, default_lon],
        zoom_start=13,
        control_scale=True
    )

    folium.Marker(
        [default_lat, default_lon],
        popup="Default Location"
    ).add_to(m)

    map_data = st_folium(
        m,
        width=None,
        height=350,
        key=key
    )

    lat = None
    lon = None

    if map_data:
        clicked = map_data.get("last_clicked")

        if clicked:
            lat = clicked.get("lat")
            lon = clicked.get("lng")

    return lat, lon


# ============================================================
# Urdu: Help requests ko map par markers ki form mein dikhaya ja raha hai.
# ============================================================
def display_help_map(help_df):
    if help_df.empty:
        st.info("Abhi koi Mohalla Help request available nahi.")
        return

    valid = help_df.dropna(
        subset=["Latitude", "Longitude"]
    ).copy()

    if valid.empty:
        st.info("Requests ke liye valid map locations available nahi.")
        return

    center_lat = float(valid["Latitude"].astype(float).mean())
    center_lon = float(valid["Longitude"].astype(float).mean())

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12
    )

    for _, row in valid.iterrows():
        status = str(row.get("Status", "Open"))

        color = "green" if status.lower() == "helped" else "red"

        popup = f"""
        <b>Problem:</b> {row.get("Problem", "")}<br>
        <b>Name:</b> {row.get("Name", "")}<br>
        <b>Status:</b> {status}<br>
        <b>Senior Citizen:</b> {row.get("Senior_Citizen", "No")}
        """

        folium.Marker(
            [
                float(row["Latitude"]),
                float(row["Longitude"])
            ],
            popup=popup,
            icon=folium.Icon(color=color, icon="info-sign")
        ).add_to(m)

    st_folium(
        m,
        width=None,
        height=450,
        key="help_requests_map"
    )


# ============================================================
# Urdu: Mohalla Bazar ke products ko 3KM radius mein map par dikhaya ja raha hai.
# ============================================================
def display_product_map(product_df, customer_lat, customer_lon):
    if product_df.empty:
        st.info("3KM ke andar koi product nahi mila.")
        return

    m = folium.Map(
        location=[customer_lat, customer_lon],
        zoom_start=13
    )

    folium.Marker(
        [customer_lat, customer_lon],
        popup="Aap ki Location",
        icon=folium.Icon(color="blue", icon="home")
    ).add_to(m)

    for _, row in product_df.iterrows():
        try:
            lat = float(row["Latitude"])
            lon = float(row["Longitude"])
        except Exception:
            continue

        points = get_user_points(row["Phone"])

        popup = f"""
        <b>Product:</b> {row["Product"]}<br>
        <b>Dukan:</b> {row["Dukan_Naam"]}<br>
        <b>Price:</b> Rs. {row["Price"]}<br>
        <b>Seller Izzat Points:</b> {points}
        """

        folium.Marker(
            [lat, lon],
            popup=popup,
            icon=folium.Icon(color="green", icon="shopping-cart")
        ).add_to(m)

    st_folium(
        m,
        width=None,
        height=450,
        key="products_map"
    )


# ============================================================
# Urdu: Product image ko optional image URL ke zariye display kiya ja raha hai.
# ============================================================
def show_product_image(url):
    if url and str(url).strip().startswith(("http://", "https://")):
        st.image(
            str(url).strip(),
            use_container_width=True
        )


# ============================================================
# Urdu: Offer list ko seller ke Izzat Points ke mutabiq sort kiya ja raha hai.
# ============================================================
def get_sorted_offers(request_id):
    offers = load_csv("offers")

    if offers.empty:
        return offers

    offers = offers[
        offers["Request_ID"].astype(str) == str(request_id)
    ].copy()

    if offers.empty:
        return offers

    offers["Seller_Izzat_Points"] = offers["Seller_Phone"].apply(
        get_user_points
    )

    offers = offers.sort_values(
        by=["Seller_Izzat_Points", "Rate"],
        ascending=[False, True]
    )

    return offers


# ============================================================
# Urdu: Home page par top 5 Mohalla Heroes display kiye ja rahe hain.
# ============================================================
def show_mohalla_heroes():
    st.subheader("🏆 Mohalla Heroes")

    users = load_csv("users")

    if users.empty:
        st.info("Abhi koi Hero available nahi.")
        return

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

    if heroes.empty:
        st.info(
            "Abhi koi Mohalla Hero nahi bana. "
            "Dusron ki madad karein aur Izzat Points hasil karein!"
        )
        return

    for rank, (_, user) in enumerate(heroes.iterrows(), start=1):
        st.markdown(
            f"""
            <div class="hero-card">
                <b>#{rank} 🤝 {user["Name"]}</b><br>
                ⭐ Izzat Points: {int(user["Izzat_Points"])}
            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# Urdu: Home page ke main buttons aur mission ko display kiya ja raha hai.
# ============================================================
def home_page():
    st.markdown(
        '<div class="main-title">🤝 IZZAT CIRCLE</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="slogan">"Madad karo, Izzat pao"</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="mission">Hamara Mission: Pehle Izzat, Phir Deal</div>',
        unsafe_allow_html=True
    )

    st.markdown("### 🌟 Hamare 5 Concepts")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            """
            <div class="concept-card">
                <div class="concept-title">🤝 Mohalla Help</div>
                <div class="concept-sub">"Ek Dosre Kaam Aao"</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            """
            <div class="concept-card">
                <div class="concept-title">🛒 Mohalla Bazar</div>
                <div class="concept-sub">"Apno Se Khareedo"</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c3:
        st.markdown(
            """
            <div class="concept-card">
                <div class="concept-title">🏪 Bare Bazar Boli</div>
                <div class="concept-sub">"Seedhi Boli, Seedha Rate"</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    c4, c5 = st.columns(2)

    with c4:
        st.markdown(
            """
            <div class="concept-card">
                <div class="concept-title">⭐ Izzat Circle System</div>
                <div class="concept-sub">"Helper Ko Izzat Aur Priority"</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c5:
        st.markdown(
            """
            <div class="concept-card">
                <div class="concept-title">❤️ Unity / Bhaichara</div>
                <div class="concept-sub">"Rat Ko Koi Bhuka Na Soye"</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()

    st.markdown("## 🚀 IZZAT CIRCLE mein kya kar sakte hain?")

    b1, b2, b3 = st.columns(3)

    with b1:
        if st.button(
            "🤝 MOHALLA HELP",
            use_container_width=True
        ):
            st.session_state["page"] = "help"
            st.rerun()

    with b2:
        if st.button(
            "🛒 MOHALLA BAZAR",
            use_container_width=True
        ):
            st.session_state["page"] = "bazar"
            st.rerun()

    with b3:
        if st.button(
            "🏪 BARE BAZAR BOLI",
            use_container_width=True
        ):
            st.session_state["page"] = "wholesale"
            st.rerun()

    st.divider()

    show_mohalla_heroes()

    st.divider()

    st.markdown(
        """
        <div class="gold-card">
        ❤️ <b>Unity / Bhaichara:</b>
        IZZAT CIRCLE ka maqsad sirf buying aur selling nahi,
        balkay mohalla ke logon ko ek doosre ki madad ke qareeb lana hai.
        <br><br>
        <b>Rat Ko Koi Bhuka Na Soye.</b>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# Urdu: Mohalla Help ka complete section yahan handle kiya ja raha hai.
# ============================================================
def mohalla_help_page():
    st.title("🤝 Mohalla Help")
    st.caption("Ek Dosre Kaam Aao")

    if st.button("⬅️ Home"):
        st.session_state["page"] = "home"
        st.rerun()

    st.divider()

    st.subheader("📍 Help Request Location")

    lat, lon = location_picker(
        "help_location_map"
    )

    if lat and lon:
        st.success(
            f"Location selected: {lat:.6f}, {lon:.6f}"
        )

    st.subheader("📝 Help Request Form")

    with st.form("help_form"):
        name = st.text_input(
            "Naam"
        )

        phone = st.text_input(
            "Phone"
        )

        problem = st.text_area(
            "Problem / Kis cheez mein madad chahiye?"
        )

        senior = st.checkbox(
            "👴 Senior Citizen Request"
        )

        senior_remarks = st.text_area(
            "Senior Citizen Remarks"
        )

        submit = st.form_submit_button(
            "📤 Help Request Submit Karein"
        )

        if submit:
            if not name or not phone or not problem:
                st.error(
                    "Naam, Phone aur Problem zaroor fill karein."
                )

            elif lat is None or lon is None:
                st.error(
                    "Map par click karke location select karein."
                )

            else:
                create_or_update_user(
                    name,
                    phone
                )

                requests = load_csv("help")

                new_request = {
                    "Request_ID": make_id("HELP"),
                    "Name": name,
                    "Phone": phone,
                    "Problem": problem,
                    "Latitude": lat,
                    "Longitude": lon,
                    "Senior_Citizen": "Yes" if senior else "No",
                    "Senior_Remarks": senior_remarks,
                    "Status": "Open",
                    "Izzat_Star": "",
                    "Helper_Phone": "",
                    "Created_At": datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                }

                requests = pd.concat(
                    [
                        requests,
                        pd.DataFrame([new_request])
                    ],
                    ignore_index=True
                )

                save_csv(
                    requests,
                    "help"
                )

                st.success(
                    "✅ Aap ki Help Request save ho gayi!"
                )

    st.divider()

    requests = load_csv("help")

    st.subheader("🗺️ Mohalla Help Requests")

    display_help_map(requests)

    if requests.empty:
        return

    st.subheader("📋 Requests List")

    for idx, row in requests.iloc[::-1].iterrows():

        status = str(row.get("Status", "Open"))

        with st.expander(
            f"🤝 {row.get('Problem', 'Help Request')} — {status}"
        ):
            st.write(
                f"**Naam:** {row.get('Name', '')}"
            )

            st.write(
                f"**Phone:** {row.get('Phone', '')}"
            )

            st.write(
                f"**Problem:** {row.get('Problem', '')}"
            )

            if str(row.get("Senior_Citizen", "")) == "Yes":
                st.warning(
                    "👴 Senior Citizen Request"
                )

                st.write(
                    f"**Remarks:** {row.get('Senior_Remarks', '')}"
                )

            if status.lower() == "open":

                st.markdown("### ❤️ Main Help Karunga")

                helper_name = st.text_input(
                    "Helper Name",
                    key=f"helper_name_{idx}"
                )

                helper_phone = st.text_input(
                    "Helper Phone",
                    key=f"helper_phone_{idx}"
                )

                if st.button(
                    "✅ Maine Help Kar Di",
                    key=f"helped_{idx}"
                ):

                    if not helper_name or not helper_phone:
                        st.error(
                            "Helper ka naam aur phone required hai."
                        )
                    else:
                        create_or_update_user(
                            helper_name,
                            helper_phone
                        )

                        requests.at[
                            idx,
                            "Status"
                        ] = "Helped"

                        requests.at[
                            idx,
                            "Helper_Phone"
                        ] = helper_phone

                        save_csv(
                            requests,
                            "help"
                        )

                        st.success(
                            "❤️ Shukriya! Aap ne mohalla member ki madad ki."
                        )

                        st.rerun()

            else:
                st.success(
                    "✅ Is request par help ho chuki hai."
                )

                current_star = row.get(
                    "Izzat_Star",
                    ""
                )

                if pd.isna(current_star) or str(current_star).strip() == "":
                    st.markdown(
                        "### ⭐ Helper ko Izzat Star dein"
                    )

                    star = st.select_slider(
                        "Izzat Star",
                        options=[1, 2, 3, 4, 5],
                        value=5,
                        key=f"star_{idx}"
                    )

                    if st.button(
                        "⭐ Rating Save Karein",
                        key=f"rate_{idx}"
                    ):

                        helper_phone = str(
                            row.get(
                                "Helper_Phone",
                                ""
                            )
                        )

                        requests.at[
                            idx,
                            "Izzat_Star"
                        ] = star

                        save_csv(
                            requests,
                            "help"
                        )

                        # Rating ko Izzat Points mein convert kiya ja raha hai.
                        change_user_points(
                            helper_phone,
                            int(star)
                        )

                        st.success(
                            f"Helper ko {star} Izzat Star mil gaye!"
                        )

                        st.rerun()

                else:
                    st.info(
                        f"⭐ Izzat Star: {current_star}/5"
                    )


# ============================================================
# Urdu: Mohalla Bazar ka complete section yahan handle kiya ja raha hai.
# ============================================================
def mohalla_bazar_page():
    st.title("🛒 Mohalla Bazar")
    st.caption("Apno Se Khareedo")

    if st.button("⬅️ Home"):
        st.session_state["page"] = "home"
        st.rerun()

    st.divider()

    st.subheader("➕ Dukaandaar Product Add Karein")

    seller_lat, seller_lon = location_picker(
        "seller_location_map"
    )

    with st.form("product_form"):
        shop = st.text_input(
            "Dukan Naam"
        )

        product = st.text_input(
            "Product"
        )

        price = st.number_input(
            "Price Rs.",
            min_value=0.0,
            step=10.0
        )

        image_url = st.text_input(
            "Image URL — Optional"
        )

        phone = st.text_input(
            "Phone"
        )

        submit_product = st.form_submit_button(
            "🛍️ Product Add Karein"
        )

        if submit_product:

            if not shop or not product or not phone:
                st.error(
                    "Dukan Naam, Product aur Phone required hain."
                )

            elif seller_lat is None or seller_lon is None:
                st.error(
                    "Map par seller ki location select karein."
                )

            else:
                create_or_update_user(
                    shop,
                    phone
                )

                products = load_csv("products")

                new_product = {
                    "Product_ID": make_id("PROD"),
                    "Dukan_Naam": shop,
                    "Product": product,
                    "Price": price,
                    "Image_URL": image_url,
                    "Phone": phone,
                    "Latitude": seller_lat,
                    "Longitude": seller_lon,
                    "Created_At": datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                }

                products = pd.concat(
                    [
                        products,
                        pd.DataFrame([new_product])
                    ],
                    ignore_index=True
                )

                save_csv(
                    products,
                    "products"
                )

                st.success(
                    "✅ Product Mohalla Bazar mein add ho gaya!"
                )

    st.divider()

    st.subheader("📍 3KM ke andar Products")

    customer_lat = st.number_input(
        "Aap ki Latitude",
        value=33.6844,
        format="%.6f"
    )

    customer_lon = st.number_input(
        "Aap ki Longitude",
        value=73.0479,
        format="%.6f"
    )

    search_products = st.button(
        "🔎 3KM Products Search Karein"
    )

    if search_products:
        products = load_csv("products")

        if products.empty:
            st.info(
                "Abhi koi product available nahi."
            )
            return

        nearby = []

        for _, row in products.iterrows():
            try:
                distance = calculate_distance_km(
                    customer_lat,
                    customer_lon,
                    row["Latitude"],
                    row["Longitude"]
                )

                if distance <= 3:
                    item = row.copy()
                    item["Distance_KM"] = round(
                        distance,
                        2
                    )
                    item["Seller_Izzat_Points"] = get_user_points(
                        row["Phone"]
                    )
                    nearby.append(item)

            except Exception:
                continue

        if not nearby:
            st.warning(
                "3KM radius mein koi product nahi mila."
            )
            return

        nearby_df = pd.DataFrame(nearby)

        nearby_df = nearby_df.sort_values(
            by=[
                "Seller_Izzat_Points",
                "Distance_KM"
            ],
            ascending=[
                False,
                True
            ]
        )

        st.success(
            f"{len(nearby_df)} products 3KM ke andar mile."
        )

        display_product_map(
            nearby_df,
            customer_lat,
            customer_lon
        )

        st.subheader("🛍️ Nearby Products")

        for _, row in nearby_df.iterrows():

            with st.container():
                col1, col2 = st.columns([1, 2])

                with col1:
                    show_product_image(
                        row.get("Image_URL", "")
                    )

                with col2:
                    st.markdown(
                        f"### 🛒 {row['Product']}"
                    )

                    st.write(
                        f"**Dukan:** {row['Dukan_Naam']}"
                    )

                    st.write(
                        f"**Price:** Rs. {row['Price']}"
                    )

                    st.write(
                        f"**Distance:** {row['Distance_KM']} KM"
                    )

                    points = int(
                        row["Seller_Izzat_Points"]
                    )

                    st.write(
                        f"⭐ **Seller Izzat Points:** {points}"
                    )

                    st.write(
                        f"📞 **Phone:** {row['Phone']}"
                    )

                    if points > 5:
                        st.success(
                            "⭐ Trusted Izzat Circle Seller"
                        )

                st.divider()


# ============================================================
# Urdu: Wholesale request ke buyer points aur Helper status display kiye ja rahe hain.
# ============================================================
def buyer_status_card(phone):
    points = get_user_points(phone)

    st.metric(
        "Aap ke Izzat Points",
        points
    )

    if points > 5:
        st.success(
            "⭐ Aap Izzat Circle Helper hain!"
        )
    else:
        st.info(
            "5 se zyada points par aap Helper ban jayenge."
        )


# ============================================================
# Urdu: Bare Bazar Boli mein new wholesale request create ki ja rahi hai.
# ============================================================
def create_wholesale_request():
    st.subheader("📝 Step 1 — Buyer Request")

    bazar = st.selectbox(
        "Bazar Select Karein",
        [
            "Raja Bazar",
            "Anarkali",
            "Urdu Bazar",
            "Jodia Bazar"
        ]
    )

    buyer_name = st.text_input(
        "Buyer Name",
        key="buyer_name"
    )

    buyer_phone = st.text_input(
        "Buyer Phone",
        key="buyer_phone"
    )

    product_name = st.text_input(
        "Product Naam",
        key="wholesale_product"
    )

    quantity = st.number_input(
        "Quantity",
        min_value=1,
        step=1,
        key="wholesale_quantity"
    )

    budget = st.number_input(
        "Budget Rs.",
        min_value=0.0,
        step=100.0,
        key="wholesale_budget"
    )

    buyer_status_card(
        buyer_phone
    )

    if st.button(
        "📤 Wholesale Request Submit Karein"
    ):

        if not buyer_name or not buyer_phone or not product_name:
            st.error(
                "Buyer Name, Phone aur Product Name required hain."
            )
            return

        create_or_update_user(
            buyer_name,
            buyer_phone
        )

        requests = load_csv("wholesale")

        new_request = {
            "Request_ID": make_id("REQ"),
            "Buyer_Name": buyer_name,
            "Buyer_Phone": buyer_phone,
            "Bazar": bazar,
            "Product_Naam": product_name,
            "Quantity": quantity,
            "Budget": budget,
            "Created_At": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        }

        requests = pd.concat(
            [
                requests,
                pd.DataFrame([new_request])
            ],
            ignore_index=True
        )

        save_csv(
            requests,
            "wholesale"
        )

        st.success(
            "✅ Buyer request successfully create ho gayi!"
        )

        st.rerun()


# ============================================================
# Urdu: Seller ke liye offer submit karne ka section banaya ja raha hai.
# ============================================================
def seller_offer_section(requests):
    st.subheader("💰 Step 2 — Seller Offer")

    if requests.empty:
        st.info(
            "Pehle koi Buyer Request honi chahiye."
        )
        return

    request_options = []

    for _, row in requests.iterrows():
        label = (
            f"{row['Request_ID']} | "
            f"{row['Bazar']} | "
            f"{row['Product_Naam']} | "
            f"Qty: {row['Quantity']}"
        )

        request_options.append(
            (
                row["Request_ID"],
                label
            )
        )

    selected_id = st.selectbox(
        "Buyer Request Select Karein",
        request_options,
        format_func=lambda x: x[1]
    )[0]

    selected = requests[
        requests["Request_ID"].astype(str) ==
        str(selected_id)
    ]

    if selected.empty:
        return

    buyer = selected.iloc[0]

    st.markdown(
        f"""
        **Bazar:** {buyer["Bazar"]}  
        **Product:** {buyer["Product_Naam"]}  
        **Quantity:** {buyer["Quantity"]}  
        **Budget:** Rs. {buyer["Budget"]}
        """
    )

    buyer_points = get_user_points(
        buyer["Buyer_Phone"]
    )

    if buyer_points > 5:
        st.markdown(
            """
            <div class="alert-member">
            🚨 YE IZZAT CIRCLE MEMBER HAI. IZZAT SE BAAT KARO
            </div>
            """,
            unsafe_allow_html=True
        )

    seller_name = st.text_input(
        "Seller Name",
        key=f"seller_name_{selected_id}"
    )

    seller_phone = st.text_input(
        "Seller Phone",
        key=f"seller_phone_{selected_id}"
    )

    seller_points = get_user_points(
        seller_phone
    )

    st.info(
        f"⭐ Aap ke Seller Izzat Points: {seller_points}"
    )

    rate = st.number_input(
        "Aap ka Rate Rs.",
        min_value=0.0,
        step=10.0,
        key=f"rate_{selected_id}"
    )

    comment = st.text_area(
        "Comment",
        key=f"comment_{selected_id}"
    )

    if st.button(
        "📨 Offer Submit Karein",
        key=f"offer_submit_{selected_id}"
    ):

        if not seller_name or not seller_phone:
            st.error(
                "Seller Name aur Phone required hain."
            )
            return

        create_or_update_user(
            seller_name,
            seller_phone
        )

        offers = load_csv("offers")

        new_offer = {
            "Offer_ID": make_id("OFF"),
            "Request_ID": selected_id,
            "Seller_Name": seller_name,
            "Seller_Phone": seller_phone,
            "Rate": rate,
            "Comment": comment,
            "Reported": "No",
            "Report_Reason": "",
            "Created_At": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        }

        offers = pd.concat(
            [
                offers,
                pd.DataFrame([new_offer])
            ],
            ignore_index=True
        )

        save_csv(
            offers,
            "offers"
        )

        st.success(
            "✅ Offer successfully submit ho gayi!"
        )

        st.rerun()


# ============================================================
# Urdu: Buyer ke liye sab offers Izzat Points ke order mein display ki ja rahi hain.
# ============================================================
def compare_offers(requests):
    st.subheader("📊 Step 3 — Buyer Offers Compare Karein")

    if requests.empty:
        st.info(
            "Abhi koi request nahi hai."
        )
        return

    request_ids = requests[
        "Request_ID"
    ].astype(str).tolist()

    selected_request = st.selectbox(
        "Request Select Karein",
        request_ids,
        key="compare_request"
    )

    request_row = requests[
        requests["Request_ID"].astype(str) ==
        selected_request
    ]

    if request_row.empty:
        return

    buyer = request_row.iloc[0]

    st.markdown(
        f"""
        ### 🛍️ {buyer["Product_Naam"]}
        **Bazar:** {buyer["Bazar"]}  
        **Quantity:** {buyer["Quantity"]}  
        **Budget:** Rs. {buyer["Budget"]}
        """
    )

    buyer_points = get_user_points(
        buyer["Buyer_Phone"]
    )

    if buyer_points > 5:
        st.markdown(
            """
            <div class="alert-member">
            🚨 YE IZZAT CIRCLE MEMBER HAI. IZZAT SE BAAT KARO
            </div>
            """,
            unsafe_allow_html=True
        )

    offers = get_sorted_offers(
        selected_request
    )

    if offers.empty:
        st.info(
            "Is request par abhi koi offer nahi aayi."
        )
        return

    st.write(
        "🏆 Offers Seller Izzat Points ke mutabiq priority mein hain."
    )

    for rank, (idx, offer) in enumerate(
        offers.iterrows(),
        start=1
    ):

        points = int(
            offer["Seller_Izzat_Points"]
        )

        reported = str(
            offer.get("Reported", "No")
        )

        if reported == "Yes":
            continue

        st.markdown(
            f"""
            <div class="gold-card">
                <h3>#{rank} — {offer["Seller_Name"]}</h3>
                <b>💰 Rate:</b> Rs. {offer["Rate"]}<br>
                <b>⭐ Seller Izzat Points:</b> {points}<br>
                <b>💬 Comment:</b> {offer["Comment"]}<br>
                <b>📞 Phone:</b> {offer["Seller_Phone"]}
            </div>
            """,
            unsafe_allow_html=True
        )

        if points > 5:
            st.success(
                "⭐ Izzat Circle Trusted Seller"
            )

        st.markdown(
            "#### 🚨 Seller Report Karein"
        )

        reason = st.selectbox(
            "Report Reason",
            [
                "Badtameezi",
                "Mehnga Rate",
                "Ghalat Information",
                "Other"
            ],
            key=f"reason_{idx}"
        )

        if st.button(
            "🚨 Report Seller",
            key=f"report_{idx}"
        ):

            offers_all = load_csv(
                "offers"
            )

            if (
                idx in offers_all.index
                and str(
                    offers_all.at[
                        idx,
                        "Reported"
                    ]
                ) != "Yes"
            ):

                offers_all.at[
                    idx,
                    "Reported"
                ] = "Yes"

                offers_all.at[
                    idx,
                    "Report_Reason"
                ] = reason

                save_csv(
                    offers_all,
                    "offers"
                )

                # Report hone par seller ke Izzat Points se 5 points minus kiye ja rahe hain.
                change_user_points(
                    offer["Seller_Phone"],
                    -5
                )

                st.error(
                    "⚠️ Seller report ho gaya aur "
                    "5 Izzat Points minus kar diye gaye."
                )

                st.rerun()


# ============================================================
# Urdu: Bare Bazar Boli ka complete section yahan handle kiya ja raha hai.
# ============================================================
def bare_bazar_boli_page():
    st.title("🏪 Bare Bazar Boli")
    st.caption("Seedhi Boli, Seedha Rate")

    if st.button("⬅️ Home"):
        st.session_state["page"] = "home"
        st.rerun()

    st.divider()

    create_wholesale_request()

    st.divider()

    requests = load_csv(
        "wholesale"
    )

    seller_offer_section(
        requests
    )

    st.divider()

    compare_offers(
        requests
    )


# ============================================================
# Urdu: Main application navigation yahan control ki ja rahi hai.
# ============================================================
def main():
    initialize_csv_files()

    if "page" not in st.session_state:
        st.session_state["page"] = "home"

    page = st.session_state["page"]

    if page == "home":
        home_page()

    elif page == "help":
        mohalla_help_page()

    elif page == "bazar":
        mohalla_bazar_page()

    elif page == "wholesale":
        bare_bazar_boli_page()

    else:
        st.session_state["page"] = "home"
        st.rerun()


# ============================================================
# Urdu: Program ko start kiya ja raha hai.
# ============================================================
if __name__ == "__main__":
    main()
