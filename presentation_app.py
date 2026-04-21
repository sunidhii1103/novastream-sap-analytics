import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# Setup page
st.set_page_config(page_title="NovaStream O2C Presentation", layout="wide")
st.title("NovaStream Electronics - Live SAP Simulation")

# Connect to the presentation database
conn = sqlite3.connect('novastream_sap.db')

try:
    st.header("Sales Performance by Plant")
    
    # Read data from the simulation tables
    df_sales = pd.read_sql("""
        SELECT WERKS as Plant, SUM(NETWR) as Revenue, COUNT(VBELN) as Orders 
        FROM NOV_VBAK 
        GROUP BY WERKS
    """, conn)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Plotly Bar Chart
        fig = px.bar(df_sales, x='Plant', y='Revenue', color='Plant', title="Total Revenue (INR) per Plant")
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        # KPI Metrics
        total_rev = df_sales['Revenue'].sum()
        total_ord = df_sales['Orders'].sum()
        st.metric("Total Revenue Simulated", f"₹ {total_rev:,.2f}")
        st.metric("Total Orders Simulated", total_ord)
        
    st.subheader("Recent ACDOCA Financial Postings (GL 600001 & 800001)")
    df_fi = pd.read_sql("SELECT BELNR as Document, RACCT as GL_Account, HSL as Amount FROM NOV_ACDOCA ORDER BY BELNR DESC LIMIT 10", conn)
    st.dataframe(df_fi, use_container_width=True)

except Exception as e:
    st.warning("No data found! Please run `python seed_sap_data.py` first to generate the simulation data.")

conn.close()
