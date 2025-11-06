# mainpage.py — Optimized Streamlit PhonePe Dashboard with Abbreviated Metrics

import streamlit as st
import pandas as pd
import plotly.express as px
from sql_connection import get_sql_connection
from insurance_insight import insurance_insights
from show_transaction_analysis import show_transaction_analysis
from show_transaction_dynamics import show_transaction_dynamics
from states_nd_districts import states_n_districts
from device_insights import device_insights
from states_n_districts_ins import states_n_districts_ins
from Heatmap import Heat_Map
from utils import helper_func



# Streamlit Config
st.set_page_config(page_title="PhonePe Project", layout="wide")

# Database Connection Caching
@st.cache_resource
def get_connection():
    conn = get_sql_connection()
    cur = conn.cursor()
    cur.execute("USE phonepe;")
    return conn

connection = get_connection()

# Data Load and Distinct Value Caching
@st.cache_data(ttl=3600)
def load_base_data():
    query = """SELECT State, Year, Quarter, Transaction_type, 
                      SUM(Transaction_count) AS Transaction_count, 
                      SUM(Transaction_amount) AS Transaction_amount
               FROM aggregated_transaction_data
               GROUP BY State, Year, Quarter, Transaction_type"""
    df = pd.read_sql(query, connection)
    return df

@st.cache_data(ttl=3600)
def get_distinct_states(df):
    return sorted(df['State'].dropna().unique().tolist())

@st.cache_data(ttl=3600)
def get_distinct_years(df):
    return sorted(df['Year'].dropna().unique().tolist())


# Visualization




def show_overview():
        st.title("📊 PhonePe Project Dashboard")
        st.subheader("Interactive Data Explorer for PhonePe Transactions")
        st.markdown("""
            This dashboard allows users to explore and analyze PhonePe transaction and user data.

            **Features**
            - Filter by State, Year, Quarter, and Transaction Type
            - View summarized metrics
            - Generate dynamic visualizations

            **Database Used:** `PhonePe.db`  
            **Created By:** `Divyansh`
        """)








# Main App Logic
def main():
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = 'Overview'

    st.sidebar.title('📂 Navigation')
    pages = {
        'Overview': show_overview,
        'Transaction Analysis': show_transaction_analysis,
        'Transaction Dynamics': show_transaction_dynamics,  
        'Transactions across States and Districts':states_n_districts,
        "User's Device Wise Insight":device_insights,
        'Insurance Insights': insurance_insights,
        'Insurance across States and Districts':states_n_districts_ins,
        "HeatMap across States":Heat_Map
        
    }
        # Set default page if not already set
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = list(pages.keys())[0]  # First page as default

    # Sidebar navigation
    for page_name in pages:
        if st.sidebar.button(page_name):
            st.session_state['current_page'] = page_name

    # Render the selected page
    pages[st.session_state['current_page']]()

if __name__ == "__main__":
    main()
