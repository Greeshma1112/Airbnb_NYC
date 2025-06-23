
import streamlit as st
import psycopg2
import folium
from streamlit_folium import st_folium

# PostgreSQL connection
conn = psycopg2.connect(
    host="",  
    dbname="",
    user="",
    password="",
    port=5432
)

st.set_page_config(layout="wide")
st.title("🔍 Safe Airbnb Listings in NYC")

# --- Sidebar Filter Form ---
with st.sidebar.form("filter_form"):
    room_type = st.selectbox("Room Type", ["", "Entire home/apt", "Private room", "Shared room"])
    max_price = st.slider("Max Price ($)", 50, 1000, 300)
    max_homicides = st.slider("Max Homicide Count in Area", 0, 10, 0)
    submitted = st.form_submit_button("Search")

# --- Run Query Only When Button Clicked ---
if submitted:
    # SQL Query
    query = f"""
    SELECT 
        l.id,
        l.host_name,
        l.price,
        l.room_type,
        n.name AS neighborhood,
        ST_X(l.listing_geom), ST_Y(l.listing_geom)
    FROM nyc_listings_bnb l
    JOIN nyc_neighborhoods n ON ST_Contains(n.geom_4326, l.listing_geom)
    LEFT JOIN nyc_homicides h ON ST_Contains(n.geom_4326, h.geom_4326)
    WHERE l.price::numeric <= %s
    {"AND l.room_type = %s" if room_type else ""}
    GROUP BY l.id, l.host_name, l.price, l.room_type, n.name, l.listing_geom
    HAVING COUNT(h.*) <= %s
    LIMIT 200;
    """

    # Parameters
    params = [max_price]
    if room_type:
        params.append(room_type)
    params.append(max_homicides)

    # Execute and store results
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    st.session_state["map_data"] = rows
    st.session_state["max_homicides"] = max_homicides

# --- Display Results ---
if "map_data" in st.session_state:
    rows = st.session_state["map_data"]
    max_homicides = st.session_state.get("max_homicides", 0)

    st.markdown(f"### ✅ Found {len(rows)} listings")

    m = folium.Map(location=[40.7128, -74.0060], zoom_start=12)

    for row in rows:
        id_, host, price, room, neighborhood, lon, lat = row
        folium.Marker(
            location=[lat, lon],
            popup=f"<b>{host}</b><br>${price}<br>{room}<br>{neighborhood}",
            icon=folium.Icon(color="green" if max_homicides == 0 else "blue")
        ).add_to(m)

    st_folium(m, width=1200, height=600)

