 
import streamlit as st
import psycopg2
import folium
from streamlit_folium import st_folium
from dotenv import load_dotenv
import os

# --- Load .env variables ---
load_dotenv()

# --- Database connection ---
conn = psycopg2.connect(
    host=os.getenv("PG_HOST"),
    dbname=os.getenv("PG_NAME"),
    user=os.getenv("PG_USER"),
    password=os.getenv("PG_PASSWORD"),
    port=int(os.getenv("PG_PORT"))
)
cur = conn.cursor()

# --- Streamlit UI ---
st.set_page_config(layout="wide")
st.title("🔍 Safe Airbnb Listings in NYC")

# --- Fetch filter options dynamically from new table ---
cur.execute("SELECT DISTINCT room_type FROM safe_airbnb_listings ORDER BY room_type;")
room_types = [""] + [row[0] for row in cur.fetchall()]

cur.execute("SELECT DISTINCT neighborhood FROM safe_airbnb_listings ORDER BY neighborhood;")
neighborhoods = [""] + [row[0] for row in cur.fetchall()]

cur.execute("SELECT MIN(price), MAX(price) FROM safe_airbnb_listings;")
min_price, max_price = cur.fetchone()

cur.execute("SELECT MAX(homicide_count) FROM safe_airbnb_listings;")
max_homicides_db = cur.fetchone()[0] or 0

# --- Sidebar filters ---
with st.sidebar.form("filter_form"):
    selected_neigh = st.selectbox("Neighborhood", neighborhoods)
    selected_room = st.selectbox("Room Type", room_types)
    price_range = st.slider("Price Range ($)", int(min_price), int(max_price), (int(min_price), int(max_price)))
    max_homicides = st.slider("Max Homicide Count in Area", 0, int(max_homicides_db), 0)
    submitted = st.form_submit_button("Search")

# --- Run query if user submits form ---
if submitted:
    query = f"""
    SELECT id,name, price, room_type, neighborhood, lon, lat, homicide_count
    FROM safe_airbnb_listings
    WHERE price BETWEEN %s AND %s
    {"AND room_type = %s" if selected_room else ""}
    {"AND neighborhood = %s" if selected_neigh else ""}
    AND homicide_count <= %s
    LIMIT 200;
    """
    
    params = [price_range[0], price_range[1]]
    if selected_room:
        params.append(selected_room)
    if selected_neigh:
        params.append(selected_neigh)
    params.append(max_homicides)

    cur.execute(query, params)
    rows = cur.fetchall()
    st.session_state["map_data"] = rows

# --- Display map ---
if "map_data" in st.session_state:
    rows = st.session_state["map_data"]
    st.markdown(f"### ✅ Found {len(rows)} listings")

    m = folium.Map(location=[40.7128, -74.0060], zoom_start=12)

    for row in rows:
        id_, host, price, room, neighborhood, lon, lat, homicide_count = row
        folium.Marker(
            location=[lat, lon],
            popup=f"<b>{host}</b><br>${price}<br>{room}<br>{neighborhood}<br>Homicides: {homicide_count}",
            icon=folium.Icon(color="green" if homicide_count == 0 else "blue")
        ).add_to(m)

    st_folium(m, width=1200, height=600)


