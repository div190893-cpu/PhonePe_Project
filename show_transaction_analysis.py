from sql_connection import get_sql_connection
from utils import helper_func
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

@st.cache_resource
def get_connection():
    conn = get_sql_connection()
    cur = conn.cursor()
    cur.execute("USE phonepe;")
    return conn

connection = get_connection()

@st.cache_data(ttl=3600)
def get_distinct_states(df):
    return sorted(df['State'].dropna().unique().tolist())

@st.cache_data(ttl=3600)
def get_distinct_years(df):
    return sorted(df['Year'].dropna().unique().tolist())


@st.cache_data(ttl=3600)
def fetch_filtered_data(state, year, quarter, transaction_type):
    df = load_base_data()
    # Apply local filters only for 'All'
    if state != 'All':
        df = df[df['State'] == state]
    if year != 'All':
        df = df[df['Year'] == int(year)]
    if quarter != 'All':
        df = df[df['Quarter'] == int(quarter)]
    if transaction_type != 'All':
        df = df[df['Transaction_type'] == transaction_type]
    return df


@st.cache_data(ttl=3600)
def load_base_data():
    query = """SELECT State, Year, Quarter, Transaction_type, 
                      SUM(Transaction_count) AS Transaction_count, 
                      SUM(Transaction_amount) AS Transaction_amount
               FROM aggregated_transaction_data
               GROUP BY State, Year, Quarter, Transaction_type"""
    df = pd.read_sql(query, connection)
    return df

def show_transaction_data_count_amount(data):
    
  
    if data.empty:
        st.warning("⚠️ No data available for the selected filters.")
        return

    # Aggregate data
    agg_data = data.groupby('Transaction_type', as_index=False).agg({
        'Transaction_count': 'sum',
        'Transaction_amount': 'sum'
    })

    # =======================
    # Transaction Count Chart
    # =======================
    count_data = agg_data.sort_values(by='Transaction_count', ascending=False)
    count_data['Transaction_count_human'] = count_data['Transaction_count'].apply(helper_func.format_number)

    fig_count = px.bar(
        count_data,
        x="Transaction_type",
        y="Transaction_count",
        color="Transaction_type",
        title="Transaction Count by Type",
        text="Transaction_count_human"
    )

    fig_count.update_traces(marker_line_width=0.3, textposition='outside')
    fig_count.update_layout(
        transition_duration=200,
        showlegend=False,
        margin=dict(l=40, r=40, t=20, b=40),
        title_x=0.5,
        xaxis_title="Transaction Type",
        yaxis_title="Transaction Count"
    )

    # Manually build Y-axis ticks in millions/billions
    y_max = count_data['Transaction_count'].max()
    step = y_max / 5 if y_max > 0 else 1
    tickvals = [i for i in range(0, int(y_max) + int(step), int(step))]

    ticktext = []
    for val in tickvals:
        if val >= 1e9:
            ticktext.append(f"{val / 1e9:.1f}B")
        elif val >= 1e6:
            ticktext.append(f"{val / 1e6:.1f}M")
        elif val >= 1e3:
            ticktext.append(f"{val / 1e3:.1f}K")
        else:
            ticktext.append(str(int(val)))

    fig_count.update_yaxes(tickvals=tickvals, ticktext=ticktext)

    # =======================
    # Transaction Amount Chart
    # =======================
    amount_data = agg_data.sort_values(by='Transaction_amount', ascending=False)
    amount_data['Transaction_amount_human'] = amount_data['Transaction_amount'].apply(helper_func.format_number)

    fig_amount = px.bar(
        amount_data,
        x="Transaction_type",
        y="Transaction_amount",
        color="Transaction_type",
        title="Transaction Amount by Type",
        text="Transaction_amount_human"
    )

    fig_amount.update_traces(marker_line_width=0.3, textposition='outside')
    fig_amount.update_layout(
        transition_duration=200,
        showlegend=False,
        margin=dict(l=40, r=40, t=20, b=40),
        title_x=0.5,
        xaxis_title="Transaction Type",
        yaxis_title="Transaction Amount"
    )

    # Same manual Y-axis tick labels (M/B)
    y_max = amount_data['Transaction_amount'].max()
    step = y_max / 5 if y_max > 0 else 1
    tickvals = [i for i in range(0, int(y_max) + int(step), int(step))]

    ticktext = []
    for val in tickvals:
        if val >= 1e9:
            ticktext.append(f"{val / 1e9:.1f}B")
        elif val >= 1e6:
            ticktext.append(f"{val / 1e6:.1f}M")
        elif val >= 1e3:
            ticktext.append(f"{val / 1e3:.1f}K")
        else:
            ticktext.append(str(int(val)))

    fig_amount.update_yaxes(tickvals=tickvals, ticktext=ticktext)

    # =======================
    # Display
    # =======================
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_count, use_container_width=True)
    with col2:
        st.plotly_chart(fig_amount, use_container_width=True)




def show_transaction_analysis():
    st.markdown(
        "<h1 style='text-align: center; font-size: 48px;'>🔍 Detailed Transaction Analysis</h1>",
        unsafe_allow_html=True
    )
    

    df = load_base_data()

    # Collapsible filter section
    with st.expander("🔧 Filter Options", expanded=True):
        # Reset button
        if st.button("🔄 Reset Filters"):
            st.session_state['selected_state'] = 'All'
            st.session_state['selected_year'] = 'All'
            st.session_state['selected_quarter'] = 'All'
            st.session_state['selected_type'] = 'All'
            st.rerun()

        # Initialize session state defaults
        if 'selected_state' not in st.session_state:
            st.session_state['selected_state'] = 'All'
        if 'selected_year' not in st.session_state:
            st.session_state['selected_year'] = 'All'
        if 'selected_quarter' not in st.session_state:
            st.session_state['selected_quarter'] = 'All'
        if 'selected_type' not in st.session_state:
            st.session_state['selected_type'] = 'All'

        # Filter options
        col1, col2, col3, col4 = st.columns(4)

        states = ['All'] + get_distinct_states(df)
        years = ['All'] + [str(y) for y in get_distinct_years(df)]
        quarters = ['All', 1, 2, 3, 4]
        types = ['All', 'Recharge & bill payments', 'Peer-to-peer payments', 'Merchant payments', 'Financial Services', 'Others']

        col1.selectbox('Select State', states, key='selected_state')
        col2.selectbox('Select Year', years, key='selected_year')
        col3.selectbox('Select Quarter', quarters, key='selected_quarter')
        col4.selectbox('Select Transaction Type', types, key='selected_type')

    # Fetch filtered data
    data = fetch_filtered_data(
        st.session_state['selected_state'],
        st.session_state['selected_year'],
        st.session_state['selected_quarter'],
        st.session_state['selected_type']
    )

    # Metrics summary
    total_transactions = data['Transaction_count'].sum() if not data.empty else 0
    average_amount = data['Transaction_amount'].mean() if not data.empty else 0
    total_amount = data['Transaction_amount'].sum() if not data.empty else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Transactions", helper_func.format_number(total_transactions))
    col2.metric("Average Transaction Amount", helper_func.format_number(average_amount))
    col3.metric("Total Transaction Amount", helper_func.format_number(total_amount))

    show_transaction_data_count_amount(data)
   
    
    

