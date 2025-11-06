from sql_connection import get_sql_connection
from utils import helper_func
import streamlit as st
import pandas as pd

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
def fetch_data(query: str) -> pd.DataFrame:
    return pd.read_sql(query, connection)

# ==========================================
# MAIN FUNCTION
# ==========================================
def states_n_districts():
    st.markdown(
        "<h1 style='text-align:center; font-size:48px;'>📍 States and Districts Level Analysis</h1>",
        unsafe_allow_html=True
    )

    # =========================================================
    # FETCH AVAILABLE YEARS + ADD "All Years"
    # =========================================================
    df_years = fetch_data("SELECT DISTINCT Year FROM aggregated_transaction_data ORDER BY Year ASC;")
    year_list = df_years["Year"].astype(str).tolist()
    year_list.insert(0, "All Years")

    # =========================================================
    # SECTION 1️⃣: TOP & LOWEST STATES / DISTRICTS
    # =========================================================
    st.markdown("## 📊 Top & Lowest Performing States/Districts")

    selected_year_toplow = st.selectbox(
        "Select Year (Top & Lowest)",
        options=year_list,
        index=1 if len(year_list) > 1 else 0,  # Default to latest numeric year
        key="toplow_year"
    )

    # Handle "All Years"
    where_clause = "" if selected_year_toplow == "All Years" else f"WHERE Year = {selected_year_toplow}"

    # ---------- Top & Bottom States ----------
    top10_query = f"""
        SELECT State, SUM(Transaction_amount) AS total_transaction_amount
        FROM aggregated_transaction_data
        {where_clause}
        GROUP BY State
        ORDER BY total_transaction_amount DESC
        LIMIT 10;
    """

    bottom10_query = f"""
        SELECT State, SUM(Transaction_amount) AS total_transaction_amount
        FROM aggregated_transaction_data
        {where_clause}
        GROUP BY State
        ORDER BY total_transaction_amount ASC
        LIMIT 10;
    """

    top10 = fetch_data(top10_query)
    bottom10 = fetch_data(bottom10_query)

    top10["Transaction Amount"] = top10["total_transaction_amount"].apply(helper_func.format_number)
    bottom10["Transaction Amount"] = bottom10["total_transaction_amount"].apply(helper_func.format_number)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏆 Top 10 States")
        st.dataframe(top10[["State", "Transaction Amount"]], use_container_width=True)
    with col2:
        st.subheader("⬇️ Bottom 10 States")
        st.dataframe(bottom10[["State", "Transaction Amount"]], use_container_width=True)

    # ---------- Top & Bottom Districts ----------
    top10_district_query = f"""
        SELECT District, State, SUM(Amount) AS total_transaction_amount
        FROM map_transaction_data
        {where_clause}
        GROUP BY District, State
        ORDER BY total_transaction_amount DESC
        LIMIT 10;
    """

    bottom10_district_query = f"""
        SELECT District, State, SUM(Amount) AS total_transaction_amount
        FROM map_transaction_data
        {where_clause}
        GROUP BY District, State
        ORDER BY total_transaction_amount ASC
        LIMIT 10;
    """

    top10_district = fetch_data(top10_district_query)
    bottom10_district = fetch_data(bottom10_district_query)

    top10_district["Transaction Amount"] = top10_district["total_transaction_amount"].apply(helper_func.format_number)
    bottom10_district["Transaction Amount"] = bottom10_district["total_transaction_amount"].apply(helper_func.format_number)

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("🏙 Top 10 Districts")
        st.dataframe(top10_district[["District", "State", "Transaction Amount"]], use_container_width=True)
    with col4:
        st.subheader("🏚 Bottom 10 Districts")
        st.dataframe(bottom10_district[["District", "State", "Transaction Amount"]], use_container_width=True)

    # =========================================================
    # SECTION 2️⃣: EMERGING & DECLINING DISTRICTS
    # =========================================================
    st.markdown("---")
    st.markdown("## 📈 Emerging vs Declining Districts (Transaction Count Growth)")

    selected_year = st.selectbox(
        "Select Year (Emerging & Declining)",
        options=year_list,
        index=1 if len(year_list) > 1 else 0,
        key="growth_year"
    )

    # Handle "All Years"
    year_filter = "" if selected_year == "All Years" else f"AND Year = {selected_year}"

    # ---------- EMERGING DISTRICTS ----------
    emerging_query = f"""
        WITH lagged_data AS (
            SELECT 
                District, 
                State, 
                Year, 
                Quarter, 
                Count AS current_txn,
                LAG(Count) OVER (
                    PARTITION BY District, State ORDER BY Year, Quarter
                ) AS previous_txn
            FROM map_transaction_data
        )
        SELECT 
            District, State, Year, Quarter,
            current_txn, previous_txn,
            ROUND(((current_txn - previous_txn) / previous_txn) * 100, 2) AS Growth_Percentage
        FROM lagged_data
        WHERE previous_txn IS NOT NULL
          AND previous_txn > 0
          AND current_txn > previous_txn
          {year_filter}
        ORDER BY Growth_Percentage DESC
        LIMIT 10;
    """

    # ---------- DECLINING DISTRICTS ----------
    declining_query = f"""
        WITH lagged_data AS (
            SELECT 
                District, 
                State, 
                Year, 
                Quarter, 
                Count AS current_txn,
                LAG(Count) OVER (
                    PARTITION BY District, State ORDER BY Year, Quarter
                ) AS previous_txn
            FROM map_transaction_data
        )
        SELECT 
            District, State, Year, Quarter,
            current_txn, previous_txn,
            ROUND(((current_txn - previous_txn) / previous_txn) * 100, 2) AS Decline_Percentage
        FROM lagged_data
        WHERE previous_txn IS NOT NULL
          AND previous_txn > 0
          AND current_txn < previous_txn
          {year_filter}
        ORDER BY Decline_Percentage ASC
        LIMIT 10;
    """

    df_emerging = fetch_data(emerging_query)
    df_declining = fetch_data(declining_query)

    col5, col6 = st.columns(2)
    with col5:
        st.subheader(f"🚀 Emerging Districts ({selected_year})")
        if not df_emerging.empty:
            df_emerging =  df_emerging = df_emerging.rename(columns={
                "Growth_Percentage": "Growth (%)",
                'previous_txn': 'Prev',
                'Quarter':'Qtr',
                'current_txn': 'Curr'
            })
            st.dataframe(
                df_emerging[['District', 'State', 'Qtr', 'Prev', 'Curr', 'Growth (%)']].style
                .format({'Growth (%)': '{:.2f}%'}).background_gradient(subset=['Growth (%)'], cmap='Greens'),
                use_container_width=True,hide_index=True
            )
        else:
            st.info("No emerging districts found for the selected year.")

    with col6:
        st.subheader(f"📉 Declining Districts ({selected_year})")
        if not df_declining.empty:
            df_declining = df_declining.rename(columns={"Decline_Percentage": "Decline (%)",
                'previous_txn': 'Prev',
                'Quarter':'Qtr',
                'current_txn': 'Curr'})
            st.dataframe(
                df_declining[['District', 'State','Qtr','Prev','Curr','Decline (%)']].style.format({'Decline (%)': '{:.2f}%'}).background_gradient(
                    subset=['Decline (%)'], cmap='Reds'),
                use_container_width=True,hide_index=True)
        else:
            st.info("No declining districts found for the selected year.")
