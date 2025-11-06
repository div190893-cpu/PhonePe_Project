from sql_connection import get_sql_connection
from utils import helper_func
import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# CONNECTION
# ==========================================
@st.cache_resource
def get_connection():
    conn = get_sql_connection()
    cur = conn.cursor()
    cur.execute("USE phonepe;")
    return conn

connection = get_connection()

# ==========================================
# DEVICE INSIGHTS PAGE
# ==========================================
def device_insights():
    st.markdown(
        "<h1 style='text-align: center; font-size: 48px;'>📱 PhonePe User's Device Dynamics Analysis</h1>",
        unsafe_allow_html=True
    )

    # ----------------------------------
    # FILTERS SECTION
    # ----------------------------------
    col1, col2, col3 = st.columns(3)

    with col1:
        years = pd.read_sql("SELECT DISTINCT year FROM aggregated_user_data ORDER BY year;", connection)
        selected_year = st.selectbox("Select Year", ["All"] + years["year"].astype(str).tolist())

    with col2:
        quarters = pd.read_sql("SELECT DISTINCT quarter FROM aggregated_user_data ORDER BY quarter;", connection)
        selected_quarter = st.selectbox("Select Quarter", ["All"] + quarters["quarter"].astype(str).tolist())

    with col3:
        states = pd.read_sql("SELECT DISTINCT state FROM aggregated_user_data ORDER BY state;", connection)
        selected_state = st.selectbox("Select State", ["All"] + states["state"].tolist())

    # ----------------------------------
    # DYNAMIC QUERY BUILDING
    # ----------------------------------
    filters = []
    if selected_year != "All":
        filters.append(f"year = {selected_year}")
    if selected_quarter != "All":
        filters.append(f"quarter = '{selected_quarter}'")
    if selected_state != "All":
        filters.append(f"state = '{selected_state}'")

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    # ----------------------------------
    # QUERIES FOR TOP AND BOTTOM 5
    # ----------------------------------
    top5_query = f"""
        SELECT brand, SUM(count) AS total_devices
        FROM aggregated_user_data
        {where_clause}
        GROUP BY brand
        ORDER BY total_devices DESC
        LIMIT 5;
    """

    bottom5_query = f"""
        SELECT brand, SUM(count) AS total_devices
        FROM aggregated_user_data
        {where_clause}
        GROUP BY brand
        ORDER BY total_devices ASC
        LIMIT 5;
    """

    top5 = pd.read_sql(top5_query, connection)
    bottom5 = pd.read_sql(bottom5_query, connection)

    # ----------------------------------
    # FORMATTING LABELS
    # ----------------------------------
    top5["formatted_label"] = top5["total_devices"].apply(helper_func.format_number)
    bottom5["formatted_label"] = bottom5["total_devices"].apply(helper_func.format_number)

    # ----------------------------------
    # VISUALS
    # ----------------------------------
    color_sequence = px.colors.qualitative.Pastel
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 5 Brands by Usage")
        fig_top = px.bar(
            top5,
            x="brand",
            y="total_devices",
            labels={"total_devices": "Device Count"},
            color="brand",
            color_discrete_sequence=color_sequence,
            text="formatted_label"
        )
        fig_top.update_traces(textposition="outside")
        fig_top.update_layout(
            showlegend=False,
            margin=dict(l=40, r=40, t=0, b=40),
            xaxis_tickangle=-45,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig_top, use_container_width=True)

    with col2:
        st.subheader("Lowest 5 Brands by Usage")
        fig_low = px.bar(
            bottom5,
            x="brand",
            y="total_devices",
            labels={"total_devices": "Device Count"},
            color="brand",
            color_discrete_sequence=color_sequence,
            text="formatted_label"
        )
        fig_low.update_traces(textposition="outside")
        fig_low.update_layout(
            showlegend=False,
            margin=dict(l=40, r=40, t=0, b=40),
            xaxis_tickangle=-45,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig_low, use_container_width=True)
