# 📊 PhonePe Data Visualization & Insights Dashboard


Analyze and visualize PhonePe Pulse data to uncover trends in transactions, user engagement, and insurance metrics — empowering data-driven decisions in the digital payments ecosystem.

## 🧠 Project Overview

A complete data engineering and analytics project built using Python, MySQL, and Streamlit, inspired by real-world PhonePe transaction and insurance datasets.
This project visualizes transaction insights, device usage trends, and insurance coverage patterns across Indian states and districts through interactive dashboards and heatmaps.

### 📈 Transaction dynamics across states & districts

### 👥 User growth and engagement

### 💼 Insurance adoption & regional patterns

### 🗺️ Interactive geo-visualizations with maps and graphs

---


## 🚀 Features

ETL Pipeline (DataETL.py)
Extracts, transforms, and loads raw data into a MySQL database.

Dynamic Dashboards (MainPage.py)
Central Streamlit interface connecting all insights in a seamless user experience.

Transaction Analysis (show_transaction_analysis.py)
Visualizes trends, transaction volume, and growth across states and years.

Transaction Dynamics (show_transaction_dynamics.py)
Displays evolving transaction patterns and types over time.

Device Insights (device_insights.py)
Analyzes transaction data across various device types.

Insurance Analytics (insurance_insight.py)
Highlights insurance trends and patterns by state and district.

Geospatial Heatmap (Heatmap.py)
Interactive choropleth map showing transaction or insurance intensity across Indian states using GeoJSON data.

Utilities (utils/)
Helper functions and reusable components such as database connectors, formatting utilities, and shared logic.

### 🗂️ Folder Structure

Phonepay/  
│  
├── Data/ ```                          # Data files (raw or processed)  
├── utils/                        # Helper scripts and utility functions  
├── .streamlit/                   # Streamlit configuration files  
│  
├── Cloning.py                    # Optional data cloning or backup logic  
├── DataETL.py                    # ETL pipeline for database population  
├── device_insights.py            # Device-level analysis  
├── file_generator.py             # File creation/export utilities  
├── Heatmap.py                    # Choropleth heatmap visualization  
├── insurance_insight.py          # Insurance analysis dashboard  
├── MainPage.py                   # Main Streamlit entry point  
├── show_transaction_analysis.py  # Transaction analytics dashboard  
├── show_transaction_dynamics.py  # Time-based transaction trends  
├── sql_connection.py             # MySQL database connection handler  
├── states_n_districts_ins.py     # Insurance data at state/district level  
├── states_nd_districts.py        # State and district-level mapping  
└── __pycache__/                  # Compiled Python files  

| Layer                    | Tools & Libraries                             |
| ------------------------ | --------------------------------------------- |
| **Frontend / Dashboard** | Streamlit, Plotly, GeoPandas                  |
| **Backend / Database**   | MySQL, SQL Connector (MySQL Connector/Python) |
| **Data Handling**        | Pandas, NumPy                                 |
| **Visualization**        | Plotly Express, Matplotlib, Folium            |
| **Automation & ETL**     | Custom Python scripts (`DataETL.py`)          |

