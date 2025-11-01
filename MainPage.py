# mainpage.py — Optimized Streamlit PhonePe Dashboard with Abbreviated Metrics

import streamlit as st
import pandas as pd
import plotly.express as px
from sql_connection import get_sql_connection
from states_nd_districts import states_n_districts
from device_insights import device_insights
from states_n_districts_ins import states_n_districts_ins
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


# Visualization

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
        margin=dict(l=40, r=40, t=40, b=40),
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
        margin=dict(l=40, r=40, t=40, b=40),
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



def show_transaction_dynamics():
    st.header("📈 PhonePe Transaction Dynamics Analysis")

    # Call your SQL data fetch functions
    df_total = get_total_transactions_state_quarter(connection)
    
    #Filtering Top 5 states
   # ----------------------------- 
    top_states = (
        df_total.groupby('State')['Total_Amount'].sum()
        .sort_values(ascending=False)
        .head(5)
        .index.tolist()
    )
    df_filtered = df_total[df_total['State'].isin(top_states)]
    # -----------------------------

  
    df_yoy = get_yoy_growth_state(connection)
    df_top_states = get_top_states(connection)

    key_states = ['Maharashtra', 'Karnataka', 'Delhi', 'Tamil Nadu', 'Uttar Pradesh']
    df_qoq = get_qoq_trends_key_states(connection, key_states)

    df_cat_share = get_transaction_category_share(connection)
    df_qoq_growth = get_qoq_growth_transaction_type(connection)
    df_declining = get_declining_states(connection)
    df_distribution = get_transaction_type_distribution(connection)

    # Plot all interactive charts with Streamlit
    plot_total_transactions_state_quarter(df_filtered)
    plot_yoy_growth_state(df_yoy)
    plot_top_states(df_top_states)
    plot_qoq_trends_key_states(df_qoq)
    plot_transaction_category_share(df_cat_share)
    plot_qoq_growth_transaction_type(df_qoq_growth)
    display_declining_states(df_declining)
    plot_transaction_type_distribution(df_distribution)


def insurance_insights():
    st.header("PhonePe Insurance Insight Analysis")
    # Number formatter with suffixes
    
    # Load top 10 states by count and amount
    query_top = """
        SELECT State, SUM(Transaction_count) AS Total_Insurance_Transactions,
            SUM(Transaction_amount) AS Total_Insurance_Amount
        FROM Aggregated_Insurance_Data
        GROUP BY State
        ORDER BY Total_Insurance_Transactions DESC
        LIMIT 10;
    """
    df_top_state = pd.read_sql(query_top, connection)

    # Load lowest 10 states by count and amount
    query_low = """
        SELECT State, SUM(Transaction_count) AS Total_Insurance_Transactions,
            SUM(Transaction_amount) AS Total_Insurance_Amount
        FROM Aggregated_Insurance_Data
        GROUP BY State
        ORDER BY Total_Insurance_Amount ASC
        LIMIT 10;
    """
    df_low_state = pd.read_sql(query_low, connection)

    # Apply formatted labels
    df_top_state['Formatted_Transactions'] = df_top_state['Total_Insurance_Transactions'].apply(helper_func.format_number)
    df_top_state['Formatted_Amount'] = df_top_state['Total_Insurance_Amount'].apply(helper_func.format_number)
    df_low_state['Formatted_Transactions'] = df_low_state['Total_Insurance_Transactions'].apply(helper_func.format_number)
    df_low_state['Formatted_Amount'] = df_low_state['Total_Insurance_Amount'].apply(helper_func.format_number)

    # Define color palette
    color_sequence = px.colors.sequential.Viridis

    # ─── Top Row ───
    top_col1, top_col2 = st.columns(2)

    with top_col1:
        st.subheader("📊 Top 10 States by Insurance Count")
        fig_top_count = px.bar(df_top_state.sort_values(by='Total_Insurance_Transactions', ascending=False),
                            x='State', y='Total_Insurance_Transactions',
                            text='Formatted_Transactions',
                            labels={'Total_Insurance_Transactions': 'Transaction Count'},
                            color='State', color_discrete_sequence=color_sequence)
        fig_top_count.update_traces(textposition='outside')
        fig_top_count.update_layout(title_text="",title_x=0.5, showlegend=False, margin=dict(l=20, r=20, t=40, b=20),
                                    xaxis_tickangle=-45)
        st.plotly_chart(fig_top_count, use_container_width=True)

    with top_col2:
        st.subheader("💰 Top 10 States by Insurance Amount")
        fig_top_amount = px.bar(df_top_state.sort_values(by='Total_Insurance_Amount', ascending=False),
                                x='State', y='Total_Insurance_Amount',
                                text='Formatted_Amount',
                                labels={'Total_Insurance_Amount': 'Transaction Amount (₹)'},
                                color='State', color_discrete_sequence=color_sequence)
        fig_top_amount.update_traces(textposition='outside')
        fig_top_amount.update_layout(title_text="",title_x=0.5, showlegend=False, margin=dict(l=20, r=20, t=40, b=20),
                                    xaxis_tickangle=-45)
        st.plotly_chart(fig_top_amount, use_container_width=True)

    # ─── Bottom Row ───
    low_col1, low_col2 = st.columns(2)

    with low_col1:
        st.subheader("📉 Lowest 10 States by Insurance Count")
        fig_low_count = px.bar(df_low_state.sort_values(by='Total_Insurance_Transactions', ascending=True),
                            x='State', y='Total_Insurance_Transactions',
                            text='Formatted_Transactions',
                            labels={'Total_Insurance_Transactions': 'Transaction Count'},
                            color='State', color_discrete_sequence=color_sequence)
        fig_low_count.update_traces(textposition='outside')
        fig_low_count.update_layout(title_x=0.5, showlegend=False, margin=dict(l=40, r=40, t=0, b=40),
                                    xaxis_tickangle=-45)
        

        st.plotly_chart(fig_low_count, use_container_width=True)

    with low_col2:
        st.subheader("🪙 Lowest 10 States by Insurance Amount")
        fig_low_amount = px.bar(df_low_state.sort_values(by='Total_Insurance_Amount', ascending=True),
                                x='State', y='Total_Insurance_Amount',
                                text='Formatted_Amount',
                                labels={'Total_Insurance_Amount': 'Transaction Amount (₹)'},
                                color='State', color_discrete_sequence=color_sequence)
        fig_low_amount.update_traces(textposition='outside')
        fig_low_amount.update_layout(title_x=0.5, showlegend=False, margin=dict(l=40, r=40, t=0, b=40),
                                    xaxis_tickangle=-45)
        st.plotly_chart(fig_low_amount, use_container_width=True)
    # Year-over-Year Growth in Insurance Transactions by State
  


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

def show_transaction_analysis():
    st.subheader("🔍 Detailed Transaction Analysis")
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
   
    
    

# 1. Total Transactions by State and Quarter
def get_total_transactions_state_quarter(connection):
    query = """
        SELECT State, Year, Quarter,
               SUM(Transaction_count) AS Total_Transactions,
               SUM(Transaction_amount) AS Total_Amount
        FROM Aggregated_Transaction_Data
        GROUP BY State, Year, Quarter
        ORDER BY Year, Quarter, Total_Amount DESC;
    """
    return pd.read_sql(query, connection)


# 2. Year-over-Year Growth by State
def get_yoy_growth_state(connection):
    query = """
        SELECT State, Year, SUM(Transaction_amount) AS Yearly_Amount,
               ROUND(
                   (SUM(Transaction_amount) - LAG(SUM(Transaction_amount)) 
                    OVER (PARTITION BY State ORDER BY Year))
                   / LAG(SUM(Transaction_amount)) 
                    OVER (PARTITION BY State ORDER BY Year) * 100, 2
               ) AS YoY_Growth_Percent
        FROM Aggregated_Transaction_Data
        GROUP BY State, Year
        ORDER BY State, Year;
    """
    return pd.read_sql(query, connection)


# 3. Top 5 States by Total Transaction Value
def get_top_states(connection):
    query = """
        SELECT State, SUM(Transaction_amount) AS Total_Transaction_Value
        FROM Aggregated_Transaction_Data
        GROUP BY State
        ORDER BY Total_Transaction_Value DESC
        LIMIT 5;
    """
    return pd.read_sql(query, connection)


# 4. Quarter-on-Quarter Trends for Selected States
def get_qoq_trends_key_states(connection, states_list):
    formatted_states = ",".join([f"'{s}'" for s in states_list])
    query = f"""
        SELECT State, CONCAT('Q', Quarter, ' ', Year) AS Time_Period,
               SUM(Transaction_amount) AS Total_Amount
        FROM Aggregated_Transaction_Data
        WHERE State IN ({formatted_states})
        GROUP BY State, Year, Quarter
        ORDER BY State, Year, Quarter;
    """
    return pd.read_sql(query, connection)


# 5. Transaction Variation Across Categories
def get_transaction_category_share(connection):
    query = """
        SELECT Transaction_type,
               SUM(Transaction_count) AS Total_Count,
               SUM(Transaction_amount) AS Total_Amount,
               ROUND(SUM(Transaction_amount) * 100.0 / 
                    (SELECT SUM(Transaction_amount) 
                     FROM Aggregated_Transaction_Data), 2) AS Share_Percent
        FROM Aggregated_Transaction_Data
        GROUP BY Transaction_type
        ORDER BY Total_Amount DESC;
    """
    return pd.read_sql(query, connection)


# 6. Quarter-Wise Growth by Transaction Type
def get_qoq_growth_transaction_type(connection):
    query = """
        SELECT Transaction_type, Year, Quarter,
               SUM(Transaction_amount) AS Total_Amount,
               ROUND(
                   (SUM(Transaction_amount) - LAG(SUM(Transaction_amount)) 
                    OVER (PARTITION BY Transaction_type ORDER BY Year, Quarter))
                   / LAG(SUM(Transaction_amount)) 
                    OVER (PARTITION BY Transaction_type ORDER BY Year, Quarter) * 100, 2
               ) AS QoQ_Growth_Percent
        FROM Aggregated_Transaction_Data
        GROUP BY Transaction_type, Year, Quarter
        ORDER BY Transaction_type, Year, Quarter;
    """
    return pd.read_sql(query, connection)


# 7. States Showing Transaction Decline
def get_declining_states(connection):
    query = """
        WITH ranked AS (
            SELECT State, Year, Quarter,
                   SUM(Transaction_amount) AS Total_Amount,
                   LAG(SUM(Transaction_amount)) 
                        OVER (PARTITION BY State ORDER BY Year, Quarter) AS Prev_Quarter_Amount
            FROM Aggregated_Transaction_data
            GROUP BY State, Year, Quarter
        )
        SELECT * FROM ranked
        WHERE Total_Amount < Prev_Quarter_Amount;
    """
    return pd.read_sql(query, connection)


# 8. Transaction Type Distribution by Region
def get_transaction_type_distribution(connection):
    query = """
        SELECT State, Transaction_type,
               SUM(Transaction_amount) AS Total_Amount,
               ROUND(SUM(Transaction_amount) * 100.0 / 
                     SUM(SUM(Transaction_amount)) OVER (PARTITION BY State), 2) AS Percent_Share
        FROM Aggregated_Transaction_Data
        GROUP BY State, Transaction_type
        ORDER BY State, Percent_Share DESC;
    """
    return pd.read_sql(query, connection)



# 1. Total Transactions by State and Quarter - Bar Chart
def plot_total_transactions_state_quarter(df):
    if df.empty:
        st.warning("No data available.")
        return
    fig = px.bar(
        df,
        x="Quarter",
        y="Total_Amount",
        color="State",
        barmode="group",
        facet_col="Year",
        title="Total Transaction Amount by State and Quarter(Top 5 States)"
    )
    st.plotly_chart(fig, use_container_width=True)


# 2. Year-over-Year Growth by State - Line Chart
def plot_yoy_growth_state(df):
    if df.empty:
        st.warning("No data available.")
        return
    fig = px.line(
        df, 
        x="Year", 
        y="YoY_Growth_Percent", 
        color="State",
        markers=True,
        title="Year-over-Year Transaction Amount Growth (%) by State"
    )
    st.plotly_chart(fig, use_container_width=True)


# 3. Top 5 States by Total Transaction Value - Pie Chart
def plot_top_states(df):
    if df.empty:
        st.warning("No data available.")
        return
    fig = px.pie(
        df, 
        names="State", 
        values="Total_Transaction_Value",
        title="Top 5 States by Total Transaction Value"
    )
    st.plotly_chart(fig, use_container_width=True)


# 4. Quarter-on-Quarter Trends for Selected States - Line Chart
def plot_qoq_trends_key_states(df):
    if df.empty:
        st.warning("No data available.")
        return
    fig = px.line(
        df,
        x="Time_Period", 
        y="Total_Amount", 
        color="State",
        markers=True,
        title="Quarter-on-Quarter Transaction Amount Trends for Selected States"
    )
    st.plotly_chart(fig, use_container_width=True)


# 5. Transaction Variation Across Categories - Bar Chart
def plot_transaction_category_share(df):
    if df.empty:
        st.warning("No data available.")
        return
    fig = px.bar(
        df,
        x="Transaction_type",
        y="Total_Amount",
        text="Share_Percent",
        title="Transaction Amount Share Across Payment Categories"
    )
    fig.update_traces(texttemplate='%{text}%', textposition='outside')
    st.plotly_chart(fig, use_container_width=True)


# 6. Quarter-Wise Growth by Transaction Type - Line Chart 
def plot_qoq_growth_transaction_type(df):
    if df.empty:
        st.warning("No data available.")
        return
    fig = px.line(
        df, 
        x=df.apply(lambda x: f'Q{x.Quarter} {x.Year}', axis=1),
        y="QoQ_Growth_Percent", 
        color="Transaction_type",
        markers=True,
        title="Quarter-on-Quarter Growth (%) by Transaction Type"
    )
    st.plotly_chart(fig, use_container_width=True)


# 7. States Showing Transaction Decline - Table Display
def display_declining_states(df):
    if df.empty:
        st.info("No states currently show transaction decline.")
        return
    st.title("Declining States")
    st.dataframe(df)


# 8. Transaction Type Distribution by Region - Stacked Bar Chart
def plot_transaction_type_distribution(df):
    if df.empty:
        st.warning("No data available.")
        return
    fig = px.bar(
        df,
        x="State",
        y="Percent_Share",
        color="Transaction_type",
        title="Transaction Type Distribution by Region",
        labels={"Percent_Share": "Percent Share (%)"},
        text=df["Percent_Share"].astype(str) + '%'
    )
    fig.update_traces(textposition='inside')
    st.plotly_chart(fig, use_container_width=True)


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
        
    }
    for page_name in pages:
        if st.sidebar.button(page_name):
            st.session_state['current_page'] = page_name

    pages[st.session_state['current_page']]()

if __name__ == "__main__":
    main()
