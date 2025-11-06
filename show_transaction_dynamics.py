from sql_connection import get_sql_connection
from utils import helper_func
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# CACHE CONNECTION
# ==========================================
@st.cache_resource
def get_connection():
    """Establish and cache database connection"""
    try:
        conn = get_sql_connection()
        cur = conn.cursor()
        cur.execute("USE phonepe;")
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

connection = get_connection()

# ==========================================
# CACHE QUERY EXECUTION
# ==========================================
@st.cache_data(ttl=200)
def fetch_data(query):
    """Fetch data with error handling"""
    if connection is None:
        st.error("No database connection available")
        return pd.DataFrame()
    
    try:
        df = pd.read_sql(query, connection)
        if df.empty:
            st.warning("Query returned no results")
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()


# ==========================================
# LINE CHART - TRANSACTION DYNAMICS
# ==========================================
def show_transaction_dynamics():
    st.markdown(
        "<h1 style='text-align: center; font-size: 48px;'>📈 PhonePe Transaction Dynamics</h1>",
        unsafe_allow_html=True
    )

    # ==========================================
    # SECTION 1: Yearly Business Trend
    # ==========================================
    st.markdown("## 📊 Yearly Business Trend")

    query1 = """
        SELECT 
            Year, SUM(transaction_amount) AS Total_Amount
        FROM Aggregated_Transaction_Data
        GROUP BY Year
        ORDER BY Year;
    """
    
    with st.spinner("Loading yearly business trend..."):
        grph1 = fetch_data(query1)
    
    if grph1.empty:
        st.warning("No data available for yearly trend")
        return

    # Format numbers using helper function
    grph1["Formatted_Value"] = grph1["Total_Amount"].apply(helper_func.format_number)

    # Create the Plotly line chart
    fig = px.line(
        grph1,
        x="Year",
        y="Total_Amount",
        markers=True,
        title="Yearly Transaction Amount Trend",
    )

    fig.update_traces(
        line=dict(color='gold', width=3),
        marker=dict(size=8, color='gold', line=dict(width=1, color='white')),
        text=grph1["Formatted_Value"],
        textposition="top center",
        customdata=grph1[["Total_Amount", "Formatted_Value"]],
        hovertemplate=(
            'Year: %{x}<br>'
            'Exact Amount: ₹%{customdata[0]:,.0f}<br>'
            'Approx: %{customdata[1]}<extra></extra>'
        ),
    )

    # Layout styling
    fig.update_layout(
        xaxis_title="Year",
        yaxis_title="Total Amount (₹)",
        title_x=0.5,
        font=dict(size=14, color="white"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        height=500,
        margin=dict(l=40, r=40, t=60, b=40),
        yaxis=dict(
            tickformat=".2s",
            showgrid=True,
            gridcolor="rgba(255,255,255,0.2)"
        ),
        xaxis=dict(
            showgrid=False,
            type='category'  # Ensures years display properly
        )
    )

    st.plotly_chart(fig, use_container_width=True)
    
    
    
    # ==========================================
    # SECTION 2: Transaction Type Trends
    # ==========================================
    st.markdown("## 💹 Yearly Trend Across Transaction Types")

    query2 = """
        SELECT 
            Year, transaction_type, SUM(transaction_amount) AS Total_Amount
        FROM Aggregated_Transaction_Data
        GROUP BY Year, transaction_type
        ORDER BY Year, transaction_type;
    """
    
    with st.spinner("Loading transaction type trends..."):
        df = fetch_data(query2)
    
    if df.empty:
        st.warning("No data available for transaction type trends")
        return

    # Format values for display
    df["Formatted_Value"] = df["Total_Amount"].apply(helper_func.format_number)

    # Add filters
    col1, col2 = st.columns([2, 1])
    with col1:
        available_types = df["transaction_type"].unique().tolist()
        selected_types = st.multiselect(
            "Filter Transaction Types",
            options=available_types,
            default=available_types,
            key="transaction_type_filter"
        )
    with col2:
        show_all = st.checkbox("Show All Years", value=True, key="show_all_years")
    
    # Filter data based on selection
    filtered_df = df[df["transaction_type"].isin(selected_types)].copy()
    
    if not show_all and len(filtered_df["Year"].unique()) > 0:
        available_years = sorted(filtered_df["Year"].unique())
        year_range = st.slider(
            "Select Year Range",
            min_value=int(available_years[0]),
            max_value=int(available_years[-1]),
            value=(int(available_years[0]), int(available_years[-1])),
            key="year_range"
        )
        filtered_df = filtered_df[
            (filtered_df["Year"] >= year_range[0]) & 
            (filtered_df["Year"] <= year_range[1])
        ]

    if filtered_df.empty:
        st.info("No data matches your filter criteria")
        return

    # Create the line chart with proper custom data
    fig2 = px.line(
        filtered_df,
        x="Year",
        y="Total_Amount",
        color="transaction_type",
        markers=True,
        title="Yearly Transaction Trends by Type",
        custom_data=["transaction_type", "Total_Amount", "Formatted_Value"]
    )

    # Update traces for better hover info
    fig2.update_traces(
        hovertemplate=(
            'Year: %{x}<br>'
            'Type: %{customdata[0]}<br>'
            'Exact Amount: ₹%{customdata[1]:,.0f}<br>'
            'Approx: %{customdata[2]}<extra></extra>'
        ),
        line=dict(width=3),
        marker=dict(size=7, line=dict(width=1, color="white")),
    )

    # Layout styling
    fig2.update_layout(
        xaxis_title="Year",
        yaxis_title="Total Amount (₹)",
        title_x=0.5,
        font=dict(size=14, color="white"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        legend_title_text="Transaction Type",
        height=550,
        margin=dict(l=40, r=40, t=60, b=40),
        yaxis=dict(
            tickformat=".2s",
            showgrid=True,
            gridcolor="rgba(255,255,255,0.2)"
        ),
        xaxis=dict(
            showgrid=False,
            type='category'
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )

    st.plotly_chart(fig2, use_container_width=True)
    
    # ==========================================
    # EMERGING AND DECLINING STATES ANALYSIS
    # ==========================================
    st.markdown("## 🚀 Emerging & 📉 Declining States Analysis")
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Growth Analysis", "🔝 Top Performers", "⚠️ Declining States"])
    
    with tab1:
        st.markdown("### Quarter-over-Quarter Performance")
        
        query_growth = """
            WITH ranked AS (
                SELECT 
                    State, 
                    Year, 
                    Quarter,
                    SUM(Transaction_amount) AS Total_Amount,
                    LAG(SUM(Transaction_amount)) 
                        OVER (PARTITION BY State ORDER BY Year, Quarter) AS Prev_Quarter_Amount
                FROM Aggregated_Transaction_data
                GROUP BY State, Year, Quarter
            )
            SELECT 
                State,
                Year,
                Quarter,
                Total_Amount,
                Prev_Quarter_Amount,
                CASE 
                    WHEN Prev_Quarter_Amount IS NOT NULL THEN
                        ((Total_Amount - Prev_Quarter_Amount) / Prev_Quarter_Amount) * 100
                    ELSE NULL
                END AS Growth_Percentage
            FROM ranked
            WHERE Prev_Quarter_Amount IS NOT NULL
            ORDER BY Year DESC, Quarter DESC, Growth_Percentage DESC;
        """
        
        with st.spinner("Analyzing state performance..."):
            growth_df = fetch_data(query_growth)
        
        if growth_df.empty:
            st.warning("No growth data available")
            return
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        with col1:
            years = sorted(growth_df["Year"].unique(), reverse=True)
            selected_year = st.selectbox("Select Year", years, key="growth_year")
        with col2:
            quarters = sorted(growth_df[growth_df["Year"] == selected_year]["Quarter"].unique(), reverse=True)
            selected_quarter = st.selectbox("Select Quarter", quarters, key="growth_quarter")
        with col3:
            min_growth = st.slider("Minimum Growth % to Display", -100, 100, -50, key="min_growth")
        
        # Filter data
        period_df = growth_df[
            (growth_df["Year"] == selected_year) & 
            (growth_df["Quarter"] == selected_quarter) &
            (growth_df["Growth_Percentage"] >= min_growth)
        ].copy()
        
        if period_df.empty:
            st.info("No data for selected period")
            return
        
        # Add formatted values
        period_df["Formatted_Amount"] = period_df["Total_Amount"].apply(helper_func.format_number)
        period_df["Formatted_Prev"] = period_df["Prev_Quarter_Amount"].apply(helper_func.format_number)
        
        # Create bar chart
        period_df = period_df.sort_values("Growth_Percentage", ascending=True)
        
        # Color code based on growth
        colors = ['red' if x < 0 else 'green' for x in period_df["Growth_Percentage"]]
        
        fig_growth = go.Figure(data=[
            go.Bar(
                y=period_df["State"],
                x=period_df["Growth_Percentage"],
                orientation='h',
                marker=dict(
                    color=colors,
                    line=dict(color='white', width=1)
                ),
                customdata=period_df[["Total_Amount", "Prev_Quarter_Amount", "Formatted_Amount", "Formatted_Prev"]],
                hovertemplate=(
                    '<b>%{y}</b><br>'
                    'Growth: %{x:.2f}%<br>'
                    'Current: ₹%{customdata[0]:,.0f} (%{customdata[2]})<br>'
                    'Previous: ₹%{customdata[1]:,.0f} (%{customdata[3]})<extra></extra>'
                )
            )
        ])
        
        fig_growth.update_layout(
            title=f"State-wise Growth for Q{selected_quarter} {selected_year}",
            xaxis_title="Growth Percentage (%)",
            yaxis_title="State",
            title_x=0.5,
            font=dict(size=12, color="white"),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=max(400, len(period_df) * 25),
            margin=dict(l=150, r=40, t=60, b=40),
            xaxis=dict(
                showgrid=True,
                gridcolor="rgba(255,255,255,0.2)",
                zeroline=True,
                zerolinecolor="rgba(255,255,255,0.5)",
                zerolinewidth=2
            ),
            yaxis=dict(showgrid=False)
        )
        
        st.plotly_chart(fig_growth, use_container_width=True)
        
        # Key insights
        col1, col2, col3 = st.columns(3)
        with col1:
            top_grower = period_df.iloc[-1]
            st.metric(
                "🚀 Highest Growth",
                top_grower["State"],
                f"+{top_grower['Growth_Percentage']:.2f}%"
            )
        with col2:
            if any(period_df["Growth_Percentage"] < 0):
                worst_decline = period_df[period_df["Growth_Percentage"] < 0].iloc[0]
                st.metric(
                    "📉 Largest Decline",
                    worst_decline["State"],
                    f"{worst_decline['Growth_Percentage']:.2f}%"
                )
        with col3:
            avg_growth = period_df["Growth_Percentage"].mean()
            st.metric(
                "📊 Average Growth",
                f"{avg_growth:.2f}%",
                "across all states"
            )
    
    with tab2:
        st.markdown("### 🏆 Top Emerging States")
        
        query_emerging = """
            WITH ranked AS (
                SELECT 
                    State, 
                    Year, 
                    Quarter,
                    SUM(Transaction_amount) AS Total_Amount,
                    LAG(SUM(Transaction_amount)) 
                        OVER (PARTITION BY State ORDER BY Year, Quarter) AS Prev_Quarter_Amount
                FROM Aggregated_Transaction_data
                GROUP BY State, Year, Quarter
            ),
            growth_calc AS (
                SELECT 
                    State,
                    Year,
                    Quarter,
                    Total_Amount,
                    Prev_Quarter_Amount,
                    CASE 
                        WHEN Prev_Quarter_Amount IS NOT NULL AND Prev_Quarter_Amount > 0 THEN
                            ((Total_Amount - Prev_Quarter_Amount) / Prev_Quarter_Amount) * 100
                        ELSE NULL
                    END AS Growth_Percentage
                FROM ranked
                WHERE Prev_Quarter_Amount IS NOT NULL
            )
            SELECT 
                State,
                AVG(Growth_Percentage) AS Avg_Growth,
                COUNT(*) AS Periods_Analyzed,
                SUM(CASE WHEN Growth_Percentage > 0 THEN 1 ELSE 0 END) AS Growth_Periods,
                MAX(Total_Amount) AS Peak_Amount
            FROM growth_calc
            GROUP BY State
            HAVING AVG(Growth_Percentage) > 0
            ORDER BY Avg_Growth DESC
            LIMIT 15;
        """
        
        with st.spinner("Identifying top performers..."):
            emerging_df = fetch_data(query_emerging)
        
        if not emerging_df.empty:
            emerging_df["Formatted_Peak"] = emerging_df["Peak_Amount"].apply(helper_func.format_number)
            emerging_df["Growth_Rate"] = (emerging_df["Growth_Periods"] / emerging_df["Periods_Analyzed"] * 100)
            
            # Display as a styled table
            st.dataframe(
                emerging_df.style.format({
                    "Avg_Growth": "{:.2f}%",
                    "Growth_Rate": "{:.2f}%",
                    "Periods_Analyzed": "{:.0f}",
                    "Growth_Periods": "{:.0f}"
                }).background_gradient(subset=["Avg_Growth"], cmap="Greens"),
                use_container_width=True,
                height=400
            )
            
            # Visual representation
            fig_emerging = px.bar(
                emerging_df.head(10),
                x="Avg_Growth",
                y="State",
                orientation='h',
                title="Top 10 Emerging States by Average Growth",
                color="Avg_Growth",
                color_continuous_scale="Greens",
                custom_data=["Avg_Growth", "Growth_Periods", "Periods_Analyzed", "Formatted_Peak"]
            )
            
            fig_emerging.update_traces(
                hovertemplate=(
                    '<b>%{y}</b><br>'
                    'Avg Growth: %{customdata[0]:.2f}%<br>'
                    'Positive Periods: %{customdata[1]}/{%{customdata[2]}<br>'
                    'Peak Amount: %{customdata[3]}<extra></extra>'
                )
            )
            
            fig_emerging.update_layout(
                font=dict(size=12, color="white"),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                height=500,
                xaxis_title="Average Growth (%)",
                yaxis_title="",
                title_x=0.5
            )
            
            st.plotly_chart(fig_emerging, use_container_width=True)
        else:
            st.info("No emerging states data available")
    
    with tab3:
        st.markdown("### ⚠️ States with Declining Trends")
        
        query_declining = """
            WITH ranked AS (
                SELECT 
                    State, 
                    Year, 
                    Quarter,
                    SUM(Transaction_amount) AS Total_Amount,
                    LAG(SUM(Transaction_amount)) 
                        OVER (PARTITION BY State ORDER BY Year, Quarter) AS Prev_Quarter_Amount
                FROM Aggregated_Transaction_data
                GROUP BY State, Year, Quarter
            )
            SELECT 
                State,
                Year,
                Quarter,
                Total_Amount,
                Prev_Quarter_Amount,
                (Total_Amount - Prev_Quarter_Amount) AS Amount_Decline,
                ((Total_Amount - Prev_Quarter_Amount) / Prev_Quarter_Amount) * 100 AS Decline_Percentage
            FROM ranked
            WHERE Total_Amount < Prev_Quarter_Amount
            ORDER BY Decline_Percentage ASC
            LIMIT 50;
        """
        
        with st.spinner("Analyzing declining trends..."):
            declining_df = fetch_data(query_declining)
        
        if not declining_df.empty:
            declining_df["Formatted_Amount"] = declining_df["Total_Amount"].apply(helper_func.format_number)
            declining_df["Formatted_Prev"] = declining_df["Prev_Quarter_Amount"].apply(helper_func.format_number)
            declining_df["Formatted_Decline"] = declining_df["Amount_Decline"].apply(helper_func.format_number)
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Declining Instances", len(declining_df))
            with col2:
                unique_states = declining_df["State"].nunique()
                st.metric("States Affected", unique_states)
            with col3:
                avg_decline = declining_df["Decline_Percentage"].mean()
                st.metric("Average Decline", f"{avg_decline:.2f}%")
            
            # Filter by severity
            severity = st.select_slider(
                "Filter by Decline Severity",
                options=["All", "Minor (<10%)", "Moderate (10-25%)", "Severe (>25%)"],
                value="All",
                key="severity_filter"
            )
            
            if severity == "Minor (<10%)":
                display_df = declining_df[declining_df["Decline_Percentage"] > -10]
            elif severity == "Moderate (10-25%)":
                display_df = declining_df[(declining_df["Decline_Percentage"] <= -10) & (declining_df["Decline_Percentage"] > -25)]
            elif severity == "Severe (>25%)":
                display_df = declining_df[declining_df["Decline_Percentage"] <= -25]
            else:
                display_df = declining_df
            
            # Display table
            st.dataframe(
                display_df[[
                    "State", "Year", "Quarter", "Formatted_Amount", 
                    "Formatted_Prev", "Formatted_Decline", "Decline_Percentage"
                ]].rename(columns={
                    "Formatted_Amount": "Current Amount",
                    "Formatted_Prev": "Previous Amount",
                    "Formatted_Decline": "Decline",
                    "Decline_Percentage": "Decline %"
                }).style.format({
                    "Decline %": "{:.2f}%"
                }).background_gradient(subset=["Decline %"], cmap="Reds_r"),
                use_container_width=True,
                height=400
            )
            
            # State-wise decline count
            state_decline_count = declining_df["State"].value_counts().head(10)
            
            fig_decline = px.bar(
                x=state_decline_count.values,
                y=state_decline_count.index,
                orientation='h',
                title="States with Most Decline Instances",
                labels={"x": "Number of Declining Quarters", "y": "State"},
                color=state_decline_count.values,
                color_continuous_scale="Reds"
            )
            
            fig_decline.update_layout(
                font=dict(size=12, color="white"),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                height=450,
                title_x=0.5,
                showlegend=False
            )
            
            st.plotly_chart(fig_decline, use_container_width=True)
        else:
            st.success("🎉 No declining trends detected - all states showing growth!")
