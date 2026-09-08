import os
import uuid
from datetime import datetime

import pandas as pd
import streamlit as st
import folium
from geopy.distance import geodesic
from streamlit_folium import st_folium


# Urdu: App ki basic settings aur page layout yahan set ki ja rahi hain.
st.set_page_config(
    page_title="IZZAT CIRCLE",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_NAME = "IZZAT CIRCLE"
DATA_FILES = {
    "users": "users.csv",
    "help": "help_requests.csv",
    "products": "products.csv",
    "wholesale": "wholesale_requests.csv",
    "offers": "offers.csv",
}

# Urdu: CSV files ke required columns yahan define kiye ja rahe hain.
CSV_SCHEMAS = {
    "users": [
        "User_ID", "Name", "Phone", "Izzat_Points", "Created_At"
    ],
    "help": [
        "Request_ID", "Name", "Phone", "Problem",
        "Latitude", "Longitude", "Status",
        "Izzat_Star", "Helper_Phone",
        "Senior_Citizen", "Senior_Remarks", "Created_At"
    ],
    "products": [
        "Product_ID", "Dukan_Naam", "Product", "Price",
        "Image_URL", "Phone", "Latitude", "Longitude", "Created_At"
    ],
    "wholesale": [
        "Request_ID", "Buyer_Name", "Buyer_Phone", "Bazar",
        "Product_Naam", "Quantity", "Budget", "Created_At"
    ],
    "offers": [
        "Offer_ID", "Request_ID", "Seller_Name", "Seller_Phone",
        "Rate", "Comment", "Reported", "Report_Reason", "Created_At"
    ],
}

# Urdu: Green aur Golden theme ke liye custom CSS yahan apply ki ja rahi hai.
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #f5fff8 0%, #ffffff 100%);
    }

    [data-testid="stSidebar"] {
        background: #073b22;
    }

    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }

    .brand {
        text-align: center;
        color: #075e32;
        font-size: 46px;
        font-weight: 900;
        letter-spacing: 1px;
        margin-bottom: 2px;
    }

    .slogan {
        text-align: center;
        color: #b8860b;
        font-size: 19px;
        font-weight: 800;
        margin-bottom: 12px;
    }

    .mission {
        background: linear-gradient(90deg, #075e32, #0b7a43);
        color: white;
        padding: 15px;
        border-radius: 15px;
        text-align: center;
        font-weight: 900;
        font-size: 18px;
        margin-bottom: 18px;
    }

    .hero-card {
        background: white;
        border: 2px solid #d4af37;
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 3px 12px rgba(0,0,0,.07);
        height: 100%;
    }

    .hero-rank {
        color: #b8860b;
        font-size: 24px;
        font-weight: 900;
    }

    .helper-alert {
        background: #ffe6e6;
        border: 2px solid #d00000;
        color: #a00000;
        padding: 15px;
        border-radius: 12px;
        font-weight: 900;
        margin: 10px 0;
    }

    .score {
        color: #b8860b;
        font-weight: 900;
    }

    div.stButton > button,
    div.stFormSubmitButton > button {
        width: 100%;
        border-radius: 11px;
        font-weight: 800;
    }

    @media (max-width: 768px) {
        .brand { font-size: 32px; }
        .slogan { font-size: 16px; }
        .mission { font-size: 15px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# Urdu: Har required CSV file ko pehli dafa automatically create kiya ja raha hai.
def initialize_csv_files():
    for key, filename in DATA_FILES.items():
        if not os.path.exists(filename):
            pd.DataFrame(
                columns=CSV_SCHEMAS[key]
            ).to_csv(
                filename,
                index=False,
                encoding="utf-8-sig"
            )


# Urdu: CSV file ko safely DataFrame mein load kiya ja raha hai.
def load_csv(key):
    filename = DATA_FILES[key]
    try:
        df = pd.read_csv(
            filename,
            encoding="utf-8-sig"
        )
    except Exception:
        df = pd.DataFrame()

    return df


# Urdu: DataFrame ko required CSV file mein save kiya ja raha hai.
def save_csv(key, df):
    df.to_csv(
        DATA_FILES[key],
        index=False,
        encoding="utf-8-sig"
    )


# Urdu: User ko users.csv mein create ya update kiya ja raha hai.
def upsert_user(name, phone):
    users = load_csv("users")

    if users.empty:
        users = pd.DataFrame(
            columns=CSV_SCHEMAS["users"]
        )

    phone = str(phone).strip()
    name = str(name).strip()

    if not phone:
        return

    if "Phone" not in users.columns:
        users = pd.DataFrame(
            columns=CSV_SCHEMAS["users"]
        )

    mask = (
        users["Phone"].astype(str).str.strip()
        == phone
    )

    if mask.any():
        users.loc[mask, "Name"] = name
    else:
        new_user = {
            "User_ID": "USR-" + uuid.uuid4().hex[:8].upper(),
            "Name": name,
            "Phone": phone,
            "Izzat_Points": 0,
            "Created_At": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }

        users = pd.concat(
            [
                users,
                pd.DataFrame([new_user])
            ],
            ignore_index=True
        )

    save_csv("users", users)


# Urdu: Phone number ke zariye user ka Izzat Score nikala ja raha hai.
def get_izzat_points(phone):
    users = load_csv("users")

    if users.empty or "Phone" not in users.columns:
        return 0

    mask = (
        users["Phone"].astype(str).str.strip()
        == str(phone).strip()
    )

    if not mask.any():
        return 0

    try:
        return int(
            float(
                users.loc[
                    mask,
                    "Izzat_Points"
                ].iloc[0]
            )
        )
    except Exception:
        return 0


# Urdu: User ke Izzat Points mein positive ya negative points change kiye ja rahe hain.
def change_izzat_points(phone, points):
    users = load_csv("users")

    if users.empty or "Phone" not in users.columns:
        return False

    mask = (
        users["Phone"].astype(str).str.strip()
        == str(phone).strip()
    )

    if not mask.any():
        return False

    idx = users.index[mask][0]

    try:
        current = int(
            float(
                users.at[
                    idx,
                    "Izzat_Points"
                ]
            )
        )
    except Exception:
        current = 0

    users.at[
        idx,
        "Izzat_Points"
    ] = max(
        0,
        current + int(points)
    )

    save_csv("users", users)
    return True


# Urdu: 5 se zyada Izzat Points walay user ko Helper identify kiya ja raha hai.
def is_helper(phone):
    return get_izzat_points(phone) > 5


# Urdu: Do locations ke darmiyan geodesic distance kilometers mein calculate ki ja rahi hai.
def distance_km(lat1, lon1, lat2, lon2):
    try:
        return geodesic(
            (float(lat1), float(lon1)),
            (float(lat2), float(lon2))
        ).km
    except Exception:
        return float("inf")


# Urdu: Map par click se live latitude aur longitude hasil kiye ja rahe hain.
def live_location_map(
    map_key,
    center_lat=33.6844,
    center_lon=73.0479,
    zoom=13,
    markers=None
):
    map_object = folium.Map(
        location=[
            center_lat,
            center_lon
        ],
        zoom_start=zoom,
        control_scale=True
    )

    if markers:
        for marker in markers:
            popup = folium.Popup(
                marker["popup"],
                max_width=320
            )

            folium.Marker(
                [
                    marker["lat"],
                    marker["lon"]
                ],
                popup=popup,
                tooltip=marker.get(
                    "tooltip",
                    marker["popup"]
                ),
                icon=folium.Icon(
                    color=marker.get(
                        "color",
                        "green"
                    ),
                    icon=marker.get(
                        "icon",
                        "info-sign"
                    )
                )
            ).add_to(map_object)

    st_folium(
        map_object,
        width=None,
        height=480,
        key=map_key,
        returned_objects=[
            "last_clicked"
        ]
    )

    # Urdu: Streamlit session state mein map ka last clicked point read kiya ja raha hai.
    map_state = st.session_state.get(
        f"_{map_key}"
    )

    if map_state:
        clicked = map_state.get(
            "last_clicked"
        )
        if clicked:
            return (
                clicked.get("lat"),
                clicked.get("lng")
            )

    return None, None


# Urdu: Folium map result se click location hasil karne ka alternate reliable helper yahan hai.
def get_map_click(
    map_key,
    center_lat,
    center_lon,
    zoom,
    markers=None
):
    map_object = folium.Map(
        location=[
            center_lat,
            center_lon
        ],
        zoom_start=zoom,
        control_scale=True
    )

    if markers:
        for marker in markers:
            folium.Marker(
                [
                    marker["lat"],
                    marker["lon"]
                ],
                popup=folium.Popup(
                    marker["popup"],
                    max_width=320
                ),
                tooltip=marker.get(
                    "tooltip",
                    "Details"
                ),
                icon=folium.Icon(
                    color=marker.get(
                        "color",
                        "green"
                    ),
                    icon=marker.get(
                        "icon",
                        "info-sign"
                    )
                )
            ).add_to(map_object)

    map_data = st_folium(
        map_object,
        width=None,
        height=480,
        key=map_key
    )

    if map_data and map_data.get("last_clicked"):
        point = map_data["last_clicked"]
        return (
            float(point["lat"]),
            float(point["lng"])
        )

    return None, None


# Urdu: Home style header aur Mohalla Heroes ko har page par Unity ke taur par dikhaya ja raha hai.
def show_header():
    st.markdown(
        f'<div class="brand">🤝 {APP_NAME}</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="slogan">Madad karo, Izzat pao</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="mission">Hamara Mission: Pehle Izzat, Phir Deal</div>',
        unsafe_allow_html=True
    )

    users = load_csv("users")

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

        if not heroes.empty:
            st.subheader("🏆 Mohalla Heroes")
            cols = st.columns(5)

            for position, (_, hero) in enumerate(
                heroes.iterrows(),
                start=1
            ):
                with cols[position - 1]:
                    st.markdown(
                        f"""
                        <div class="hero-card">
                            <div class="hero-rank">#{position}</div>
                            <b>🤝 {hero["Name"]}</b>
                            <br>
                            <span class="score">
                            ⭐ {int(hero["Izzat_Points"])} Izzat Points
                            </span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )


# Urdu: Mohalla Help ki requests ko 3KM radius mein filter aur map par show kiya ja raha hai.
def mohalla_help():
    st.header("🤝 MOHALLA HELP")
    st.caption("Ek Dosre Kaam Aao — 3KM ke andar help requests")

    st.info(
        "📍 Neeche map par apni location par click karein. "
        "Sirf 3KM ke andar ki open help requests dikhengi."
    )

    user_lat, user_lon = get_map_click(
        "help_live_map",
        33.6844,
        73.0479,
        13
    )

    if user_lat is not None:
        st.success(
            f"📍 Your Pin: {user_lat:.6f}, {user_lon:.6f}"
        )

    with st.form("help_request_form"):
        st.subheader("🆘 Help Request")

        c1, c2 = st.columns(2)

        with c1:
            name = st.text_input("Naam")
            phone = st.text_input("Phone")

        with c2:
            senior = st.checkbox(
                "👴 Senior Citizen Request"
            )
            senior_remarks = st.text_input(
                "Senior Citizen Remarks"
            )

        problem = st.text_area(
            "Problem / Kis madad ki zaroorat hai?"
        )

        submit = st.form_submit_button(
            "📤 Help Request Post Karein"
        )

    if submit:
        if not name.strip() or not phone.strip():
            st.error(
                "Naam aur Phone required hain."
            )
        elif not problem.strip():
            st.error(
                "Problem likhna zaroori hai."
            )
        elif user_lat is None:
            st.error(
                "Map par apni location pin karein."
            )
        else:
            upsert_user(
                name,
                phone
            )

            requests = load_csv("help")

            new_request = {
                "Request_ID": "HELP-" + uuid.uuid4().hex[:8].upper(),
                "Name": name.strip(),
                "Phone": phone.strip(),
                "Problem": problem.strip(),
                "Latitude": user_lat,
                "Longitude": user_lon,
                "Status": "Open",
                "Izzat_Star": "",
                "Helper_Phone": "",
                "Senior_Citizen": "Yes" if senior else "No",
                "Senior_Remarks": senior_remarks.strip(),
                "Created_At": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            }

            requests = pd.concat(
                [
                    requests,
                    pd.DataFrame([new_request])
                ],
                ignore_index=True
            )

            save_csv(
                "help",
                requests
            )

            st.success(
                "✅ Help request save ho gayi."
            )
            st.rerun()

    st.divider()
    st.subheader("📍 3KM ke andar Help Requests")

    requests = load_csv("help")

    if requests.empty:
        st.info(
            "Abhi koi help request available nahi."
        )
        return

    if user_lat is None:
        st.warning(
            "Nearby requests dekhne ke liye map par pin karein."
        )
        return

    open_requests = requests[
        requests["Status"].astype(str) == "Open"
    ].copy()

    if open_requests.empty:
        st.success(
            "Koi open help request nahi."
        )
        return

    nearby = []

    for _, row in open_requests.iterrows():
        dist = distance_km(
            user_lat,
            user_lon,
            row["Latitude"],
            row["Longitude"]
        )

        if dist <= 3:
            nearby.append(
                (
                    row,
                    round(dist, 2)
                )
            )

    if not nearby:
        st.info(
            "3KM ke andar koi open help request nahi mili."
        )
        return

    markers = []

    for row, dist in nearby:
        senior_text = (
            "Yes"
            if str(row["Senior_Citizen"]).lower()
            == "yes"
            else "No"
        )

        markers.append(
            {
                "lat": float(row["Latitude"]),
                "lon": float(row["Longitude"]),
                "tooltip": f"{row['Name']} — {dist} KM",
                "popup": (
                    f"<b>🤝 {row['Name']}</b><br>"
                    f"Problem: {row['Problem']}<br>"
                    f"Distance: {dist} KM<br>"
                    f"Senior Citizen: {senior_text}<br>"
                    f"Remarks: {row['Senior_Remarks']}"
                ),
                "color": "red",
                "icon": "plus"
            }
        )

    get_map_click(
        "help_requests_map",
        user_lat,
        user_lon,
        13,
        markers
    )

    for row, dist in nearby:
        st.markdown(
            f"### 🤝 {row['Name']} — {dist} KM"
        )
        st.write(
            f"**Problem:** {row['Problem']}"
        )

        if str(row["Senior_Citizen"]).lower() == "yes":
            st.warning(
                f"👴 Senior Citizen: {row['Senior_Remarks']}"
            )

        with st.expander(
            "⭐ Help Complete / Izzat Star"
        ):
            helper_name = st.text_input(
                "Helper Name",
                key=f"helper_name_{row['Request_ID']}"
            )

            helper_phone = st.text_input(
                "Helper Phone",
                key=f"helper_phone_{row['Request_ID']}"
            )

            if st.button(
                "🤝 Main ne help kar di",
                key=f"complete_{row['Request_ID']}"
            ):
                if not helper_name.strip() or not helper_phone.strip():
                    st.error(
                        "Helper Name aur Phone required hain."
                    )
                else:
                    upsert_user(
                        helper_name,
                        helper_phone
                    )

                    requests = load_csv("help")
                    mask = (
                        requests["Request_ID"].astype(str)
                        == str(row["Request_ID"])
                    )

                    requests.loc[
                        mask,
                        "Status"
                    ] = "Completed"

                    requests.loc[
                        mask,
                        "Helper_Phone"
                    ] = helper_phone.strip()

                    save_csv(
                        "help",
                        requests
                    )

                    st.success(
                        "Help complete mark ho gayi."
                    )

                    st.session_state[
                        f"rate_request_{row['Request_ID']}"
                    ] = True

                    st.rerun()

            if st.session_state.get(
                f"rate_request_{row['Request_ID']}",
                False
            ):
                star = st.slider(
                    "Izzat Star",
                    1,
                    5,
                    5,
                    key=f"star_{row['Request_ID']}"
                )

                if st.button(
                    "⭐ Izzat Star Save Karein",
                    key=f"save_star_{row['Request_ID']}"
                ):
                    requests = load_csv("help")
                    mask = (
                        requests["Request_ID"].astype(str)
                        == str(row["Request_ID"])
                    )

                    requests.loc[
                        mask,
                        "Izzat_Star"
                    ] = int(star)

                    save_csv(
                        "help",
                        requests
                    )

                    # Urdu: Helper ko milne wali star rating ko Izzat Points mein add kiya ja raha hai.
                    change_izzat_points(
                        helper_phone,
                        int(star)
                    )

                    st.success(
                        f"⭐ {star} Izzat Stars save ho gaye."
                    )

                    st.session_state.pop(
                        f"rate_request_{row['Request_ID']}",
                        None
                    )

                    st.rerun()


# Urdu: Mohalla Bazar mein seller products add aur customer ke 3KM nearby products show kiye ja rahe hain.
def mohalla_bazar():
    st.header("🛍️ MOHALLA BAZAR")
    st.caption("Apno Se Khareedo — 3KM ke andar local products")

    st.subheader("➕ Seller Product Add Karein")

    seller_lat, seller_lon = get_map_click(
        "seller_pin_map",
        33.6844,
        73.0479,
        13
    )

    if seller_lat is not None:
        st.success(
            f"📍 Seller Pin: {seller_lat:.6f}, {seller_lon:.6f}"
        )

    with st.form("product_form"):
        c1, c2 = st.columns(2)

        with c1:
            shop_name = st.text_input(
                "Dukan Naam"
            )
            seller_phone = st.text_input(
                "Seller Phone"
            )
            product_name = st.text_input(
                "Product"
            )

        with c2:
            price = st.number_input(
                "Price (Rs.)",
                min_value=0.0,
                step=10.0
            )
            image_url = st.text_input(
                "Image URL — Optional"
            )

        add_product = st.form_submit_button(
            "🛒 Product Add Karein"
        )

    if add_product:
        if (
            not shop_name.strip()
            or not seller_phone.strip()
            or not product_name.strip()
        ):
            st.error(
                "Dukan, Seller Phone aur Product required hain."
            )
        elif seller_lat is None:
            st.error(
                "Product ki location map par pin karein."
            )
        else:
            upsert_user(
                shop_name,
                seller_phone
            )

            products = load_csv("products")

            new_product = {
                "Product_ID": "PROD-" + uuid.uuid4().hex[:8].upper(),
                "Dukan_Naam": shop_name.strip(),
                "Product": product_name.strip(),
                "Price": price,
                "Image_URL": image_url.strip(),
                "Phone": seller_phone.strip(),
                "Latitude": seller_lat,
                "Longitude": seller_lon,
                "Created_At": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            }

            products = pd.concat(
                [
                    products,
                    pd.DataFrame([new_product])
                ],
                ignore_index=True
            )

            save_csv(
                "products",
                products
            )

            st.success(
                "✅ Product Mohalla Bazar mein add ho gaya."
            )
            st.rerun()

    st.divider()
    st.subheader("📍 Customer Location")

    customer_lat, customer_lon = get_map_click(
        "customer_bazar_map",
        33.6844,
        73.0479,
        13
    )

    if customer_lat is None:
        st.info(
            "Map par apna customer pin lagayein; phir 3KM products neeche show honge."
        )
        return

    st.success(
        f"📍 Customer Pin: {customer_lat:.6f}, {customer_lon:.6f}"
    )

    products = load_csv("products")

    if products.empty:
        st.info(
            "Abhi koi product available nahi."
        )
        return

    nearby = []

    for _, row in products.iterrows():
        dist = distance_km(
            customer_lat,
            customer_lon,
            row["Latitude"],
            row["Longitude"]
        )

        if dist <= 3:
            nearby.append(
                (
                    row,
                    round(dist, 2)
                )
            )

    st.subheader("🛍️ 3KM ke andar Products")

    if not nearby:
        st.warning(
            "3KM ke andar koi product nahi mila."
        )
        return

    markers = []

    for row, dist in nearby:
        score = get_izzat_points(
            row["Phone"]
        )

        markers.append(
            {
                "lat": float(row["Latitude"]),
                "lon": float(row["Longitude"]),
                "tooltip": (
                    f"{row['Product']} — "
                    f"{dist} KM"
                ),
                "popup": (
                    f"<b>{row['Product']}</b><br>"
                    f"Dukan: {row['Dukan_Naam']}<br>"
                    f"Price: Rs. {float(row['Price']):,.0f}<br>"
                    f"Izzat Score: ⭐ {score}<br>"
                    f"Phone: {row['Phone']}<br>"
                    f"Distance: {dist} KM"
                ),
                "color": "green",
                "icon": "shopping-cart"
            }
        )

    get_map_click(
        "nearby_products_map",
        customer_lat,
        customer_lon,
        13,
        markers
    )

    for row, dist in nearby:
        score = get_izzat_points(
            row["Phone"]
        )

        with st.container(border=True):
            c1, c2 = st.columns([1, 2])

            with c1:
                if str(row["Image_URL"]).strip():
                    st.image(
                        row["Image_URL"],
                        use_container_width=True
                    )
                else:
                    st.markdown(
                        "### 🛍️"
                    )

            with c2:
                st.markdown(
                    f"### {row['Product']}"
                )
                st.write(
                    f"**Dukan:** {row['Dukan_Naam']}"
                )
                st.write(
                    f"**Price:** Rs. {float(row['Price']):,.0f}"
                )
                st.markdown(
                    f'<span class="score">⭐ Seller Izzat Score: {score}</span>',
                    unsafe_allow_html=True
                )
                st.write(
                    f"📍 Distance: {dist} KM"
                )


# Urdu: Bare Bazar Boli mein buyer request create, sellers offers submit aur offers compare kiye ja rahe hain.
def bare_bazar_boli():
    st.header("🏪 BARE BAZAR BOLI")
    st.caption("Seedhi Boli, Seedha Rate")

    bazars = [
        "Raja Bazar",
        "Anarkali",
        "Urdu Bazar",
        "Jodia Bazar"
    ]

    st.subheader("1️⃣ Buyer Request")

    with st.form("wholesale_request_form"):
        c1, c2 = st.columns(2)

        with c1:
            buyer_name = st.text_input(
                "Buyer Name"
            )
            buyer_phone = st.text_input(
                "Buyer Phone"
            )
            bazar = st.selectbox(
                "Bazar Select Karein",
                bazars
            )

        with c2:
            product_name = st.text_input(
                "Product Naam"
            )
            quantity = st.number_input(
                "Quantity",
                min_value=1,
                step=1
            )
            budget = st.number_input(
                "Budget (Rs.)",
                min_value=0.0,
                step=100.0
            )

        create_request = st.form_submit_button(
            "📢 Boli Request Post Karein"
        )

    if create_request:
        if (
            not buyer_name.strip()
            or not buyer_phone.strip()
            or not product_name.strip()
        ):
            st.error(
                "Buyer Name, Phone aur Product required hain."
            )
        else:
            upsert_user(
                buyer_name,
                buyer_phone
            )

            requests = load_csv("wholesale")

            request_id = (
                "REQ-"
                + uuid.uuid4().hex[:8].upper()
            )

            new_request = {
                "Request_ID": request_id,
                "Buyer_Name": buyer_name.strip(),
                "Buyer_Phone": buyer_phone.strip(),
                "Bazar": bazar,
                "Product_Naam": product_name.strip(),
                "Quantity": int(quantity),
                "Budget": budget,
                "Created_At": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            }

            requests = pd.concat(
                [
                    requests,
                    pd.DataFrame([new_request])
                ],
                ignore_index=True
            )

            save_csv(
                "wholesale",
                requests
            )

            st.success(
                f"📢 Request post ho gayi. Request ID: {request_id}"
            )

    st.divider()
    st.subheader("2️⃣ Active Boli Requests")

    requests = load_csv("wholesale")

    if requests.empty:
        st.info(
            "Abhi koi Boli request nahi."
        )
        return

    for _, request in requests.iloc[::-1].iterrows():
        request_id = str(
            request["Request_ID"]
        )

        buyer_phone_value = str(
            request["Buyer_Phone"]
        )

        helper = is_helper(
            buyer_phone_value
        )

        with st.container(border=True):
            st.markdown(
                f"### 🏪 {request['Product_Naam']} — {request['Bazar']}"
            )

            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.write(
                    f"**Buyer:** {request['Buyer_Name']}"
                )

            with c2:
                st.write(
                    f"**Qty:** {request['Quantity']}"
                )

            with c3:
                st.write(
                    f"**Budget:** Rs. {float(request['Budget']):,.0f}"
                )

            with c4:
                st.write(
                    f"**Request:** {request_id}"
                )

            if helper:
                st.markdown(
                    '<div class="helper-alert">🚨 YE IZZAT CIRCLE MEMBER HAI. IZZAT SE BAAT KARO</div>',
                    unsafe_allow_html=True
                )

            st.markdown("#### 💼 Seller Offer")

            with st.form(
                f"offer_form_{request_id}"
            ):
                oc1, oc2 = st.columns(2)

                with oc1:
                    seller_name = st.text_input(
                        "Seller Name",
                        key=f"seller_name_{request_id}"
                    )
                    seller_phone = st.text_input(
                        "Seller Phone",
                        key=f"seller_phone_{request_id}"
                    )

                with oc2:
                    offer_rate = st.number_input(
                        "Your Rate (Rs.)",
                        min_value=0.0,
                        step=10.0,
                        key=f"rate_{request_id}"
                    )
                    comment = st.text_input(
                        "Comment",
                        key=f"comment_{request_id}"
                    )

                submit_offer = st.form_submit_button(
                    "💰 Offer Submit Karein"
                )

            if submit_offer:
                if (
                    not seller_name.strip()
                    or not seller_phone.strip()
                ):
                    st.error(
                        "Seller Name aur Phone required hain."
                    )
                elif offer_rate <= 0:
                    st.error(
                        "Valid rate enter karein."
                    )
                else:
                    upsert_user(
                        seller_name,
                        seller_phone
                    )

                    offers = load_csv("offers")

                    new_offer = {
                        "Offer_ID": (
                            "OFF-"
                            + uuid.uuid4().hex[:8].upper()
                        ),
                        "Request_ID": request_id,
                        "Seller_Name": seller_name.strip(),
                        "Seller_Phone": seller_phone.strip(),
                        "Rate": offer_rate,
                        "Comment": comment.strip(),
                        "Reported": "No",
                        "Report_Reason": "",
                        "Created_At": datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    }

                    offers = pd.concat(
                        [
                            offers,
                            pd.DataFrame([new_offer])
                        ],
                        ignore_index=True
                    )

                    save_csv(
                        "offers",
                        offers
                    )

                    st.success(
                        "✅ Seller offer submit ho gayi."
                    )
                    st.rerun()

            st.markdown("#### 📊 Offers — Izzat Score ke hisaab se")

            offers = load_csv("offers")

            if offers.empty:
                st.info(
                    "Abhi is request par koi offer nahi."
                )
                continue

            request_offers = offers[
                offers["Request_ID"].astype(str)
                == request_id
            ].copy()

            if request_offers.empty:
                st.info(
                    "Abhi is request par koi offer nahi."
                )
                continue

            request_offers["Seller_Izzat_Points"] = (
                request_offers["Seller_Phone"]
                .apply(get_izzat_points)
            )

            request_offers = request_offers.sort_values(
                by=[
                    "Seller_Izzat_Points",
                    "Rate"
                ],
                ascending=[
                    False,
                    True
                ]
            )

            for _, offer in request_offers.iterrows():
                score = int(
                    offer["Seller_Izzat_Points"]
                )

                reported = str(
                    offer["Reported"]
                ).lower() == "yes"

                with st.container(border=True):
                    a, b, c = st.columns(
                        [2, 1, 2]
                    )

                    with a:
                        st.write(
                            f"**{offer['Seller_Name']}**"
                        )
                        st.write(
                            f"📞 {offer['Seller_Phone']}"
                        )
                        st.markdown(
                            f'<span class="score">⭐ Izzat Score: {score}</span>',
                            unsafe_allow_html=True
                        )

                    with b:
                        st.markdown(
                            f"### Rs. {float(offer['Rate']):,.0f}"
                        )

                    with c:
                        st.write(
                            offer["Comment"]
                            if str(offer["Comment"]).strip()
                            else "No comment"
                        )

                        if reported:
                            st.error(
                                "⚠️ Reported"
                            )
                        else:
                            with st.expander(
                                "🚩 Report Seller"
                            ):
                                reason = st.text_input(
                                    "Report Reason",
                                    key=f"reason_{offer['Offer_ID']}"
                                )

                                if st.button(
                                    "Report",
                                    key=f"report_{offer['Offer_ID']}"
                                ):
                                    if not reason.strip():
                                        st.error(
                                            "Report reason likhein."
                                        )
                                    else:
                                        offers = load_csv(
                                            "offers"
                                        )

                                        offer_mask = (
                                            offers["Offer_ID"].astype(str)
                                            == str(
                                                offer["Offer_ID"]
                                            )
                                        )

                                        if offer_mask.any():
                                            offers.loc[
                                                offer_mask,
                                                "Reported"
                                            ] = "Yes"

                                            offers.loc[
                                                offer_mask,
                                                "Report_Reason"
                                            ] = reason.strip()

                                            save_csv(
                                                "offers",
                                                offers
                                            )

                                            # Urdu: Report hone par seller ke Izzat Points mein se 5 points minus kiye ja rahe hain.
                                            change_izzat_points(
                                                offer["Seller_Phone"],
                                                -5
                                            )

                                            st.success(
                                                "🚩 Seller report ho gaya aur 5 Izzat Points cut ho gaye."
                                            )
                                            st.rerun()


# Urdu: Sidebar mein sirf teen required concepts ki navigation rakhi ja rahi hai.
def sidebar_navigation():
    with st.sidebar:
        st.markdown(
            "## 🤝 IZZAT CIRCLE"
        )
        st.caption(
            "Madad karo, Izzat pao"
        )

        selected = st.radio(
            "Navigation",
            [
                "Mohalla Help",
                "Mohalla Bazar",
                "Bare Bazar Boli"
            ],
            index=0
        )

        st.divider()

        st.markdown(
            "### 5 Concepts"
        )
        st.caption(
            "🤝 Mohalla Help\n\n"
            "🛍️ Mohalla Bazar\n\n"
            "🏪 Bare Bazar Boli\n\n"
            "⭐ Izzat Circle System\n\n"
            "🤲 Unity / Bhaichara"
        )

        st.divider()

        st.markdown(
            "**Pehle Izzat, Phir Deal**"
        )

    return selected


# Urdu: Main function CSV files initialize karke sirf teen pages ko run karti hai.
def main():
    initialize_csv_files()

    selected = sidebar_navigation()

    show_header()

    if selected == "Mohalla Help":
        mohalla_help()

    elif selected == "Mohalla Bazar":
        mohalla_bazar()

    elif selected == "Bare Bazar Boli":
        bare_bazar_boli()


# Urdu: App ko direct run karne par main function start ki ja rahi hai.
if __name__ == "__main__":
    main()
