from sql_connection import get_sql_connection
from utils.helper_func import normalize_state_names
from utils.helper_func import format_number
import streamlit as st
import pandas as pd
import plotly.express as px
import json
import requests

# ==========================================
# CACHE CONNECTION
# ==========================================
@st.cache_resource
def get_connection():
    conn = get_sql_connection()
    cur = conn.cursor()
    cur.execute("USE phonepe;")
    return conn

connection = get_connection()

# ==========================================
# CACHE QUERY EXECUTION
# ==========================================
@st.cache_data(ttl=200)
def fetch_data(query):
    return pd.read_sql(query, connection)


# ==========================================
# HEAT MAP FUNCTION
# ==========================================
def Heat_Map():
    # Title
    st.markdown(
        "<h1 style='text-align: center; font-size: 48px;'>📈 PhonePe Transactions Across States of India</h1>",
        unsafe_allow_html=True
    )

    # -------------------------------
    # 1️⃣ Load years
    # -------------------------------
    df_years = fetch_data("SELECT DISTINCT Year FROM Aggregated_Transaction_Data ORDER BY Year ASC;")
    year_list = df_years["Year"].astype(str).tolist()
    year_list.insert(0, "All Years")

    # -------------------------------
    # 2️⃣ Year selection
    # -------------------------------
    selected_year = st.selectbox(
        "Select Year",
        options=year_list,
        index=len(year_list) - 1 if len(year_list) > 1 else 0,
        key="heatmap_year"
    )

    # -------------------------------
    # 3️⃣ Build query
    # -------------------------------
    where_clause = "" if selected_year == "All Years" else f"WHERE Year = {selected_year}"

    query = f"""
        SELECT State, Year, SUM(transaction_amount) AS Total_Amount
        FROM Aggregated_Transaction_Data
        {where_clause}
        GROUP BY State, Year
        ORDER BY Year;
    """

    df = fetch_data(query)
    df = normalize_state_names(df, "State")

    # -------------------------------
    # 4️⃣ Load India GeoJSON
    # -------------------------------
    geojson_url = (
        "https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/"
        "raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson"
    )
    response = requests.get(geojson_url)
    india_states = json.loads(response.text)

    # -------------------------------
    # 5️⃣ Choropleth Map
    # -------------------------------
    fig = px.choropleth(
        df,
        geojson=india_states,
        featureidkey="properties.ST_NM",
        locations="State",
        color="Total_Amount",
        color_continuous_scale="Viridis",
        title=f"Transaction Volume Across India ({selected_year})",
        hover_name="State",
        hover_data={"Total_Amount": True},
    )

    # Hover and formatting
    fig.update_traces(
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Transaction Value: ₹%{z:,.0f}<br>"
            "Approx: %{text}<extra></extra>"
        ),
        text=[format_number(v) for v in df["Total_Amount"]],
        customdata=df[["State"]],
    )

    # Transparent background setup
    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor='rgba(0,0,0,0)'  # transparent geo background
    )
    fig.update_layout(
        margin=dict(r=0, t=40, l=0, b=0),
        paper_bgcolor='rgba(0,0,0,0)',  # full transparent
        plot_bgcolor='rgba(0,0,0,0)',   # transparent plot background
        coloraxis_colorbar=dict(
            title="Transaction Value (₹)",
            tickformat=".2s"
        ),
        font=dict(color="#FFFFFF") if st.get_option("theme.base") == "dark" else dict(color="#00000000")
    )
    
    fig.update_layout(
    width=1000,  # increase width
    height=800,  # increase height
    )

     # Display Map
    st.plotly_chart(fig, use_container_width=True)
    

    # -------------------------------
    # 6️⃣ Unmatched State Warning
    # -------------------------------
    geo_states = {f["properties"]["ST_NM"] for f in india_states["features"]}
    unmatched = sorted(set(df["State"]) - geo_states)

    if unmatched:
        st.warning(f"⚠️ The following states are unmatched and not shown: {', '.join(unmatched)}")

