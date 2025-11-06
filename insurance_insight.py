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

def insurance_insights():
    
    st.markdown(
        "<h1 style='text-align: center; font-size: 48px;'>📈 PhonePe Insurance</h1>",
        unsafe_allow_html=True
    )
    
    
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
        fig_top_count.update_layout(title_text="",title_x=0.5, showlegend=False, margin=dict(l=20, r=20, t=0, b=20),
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
        fig_top_amount.update_layout(title_text="",title_x=0.5, showlegend=False, margin=dict(l=20, r=20, t=0, b=20),
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
        fig_low_count.update_layout(title_x=0.5, showlegend=False, margin=dict(l=20, r=20, t=0, b=20),
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
        fig_low_amount.update_layout(title_x=0.5, showlegend=False, margin=dict(l=20, r=20, t=0, b=20),
                                    xaxis_tickangle=-45)
        st.plotly_chart(fig_low_amount, use_container_width=True)
 
  
