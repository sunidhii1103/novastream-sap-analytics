import streamlit as st
import pandas as pd
import sys
import os

# Add root to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.analytics.o2c_metrics import O2CMetrics
from src.db.connection import get_engine

st.set_page_config(page_title="NovaStream SAP Analytics", layout="wide")

st.title("NovaStream Electronics - SAP Analytics Dashboard")
st.sidebar.header("Personas")
persona = st.sidebar.radio("Select View:", ["Sales Manager", "Finance Controller", "Supply Chain"])

metrics = O2CMetrics()
engine = get_engine()

if persona == "Sales Manager":
    st.header("Sales Performance (SD Module)")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Perfect Order Rate", f"{metrics.get_perfect_order_rate():.1f}%")
    with col2:
        rev = pd.read_sql("SELECT SUM(order_amount_local) as val FROM fct_o2c_transactions", engine).iloc[0]['val']
        rev_val = rev if pd.notnull(rev) else 0
        st.metric("Total Order Volume (INR)", f"₹{rev_val:,.2f}")
    with col3:
        st.metric("Avg Lead Time", f"{metrics.get_order_lead_time():.1f} days")
        
    st.subheader("Recent Sales Orders")
    df_orders = pd.read_sql("SELECT order_id, order_date, order_amount_local, is_fully_delivered FROM fct_o2c_transactions ORDER BY order_date DESC LIMIT 10", engine)
    st.dataframe(df_orders)

elif persona == "Finance Controller":
    st.header("Financial Reconciliation (FI Module - NV01)")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Potential Revenue Leakage", f"₹{metrics.get_revenue_leakage():,.2f}")
    with col2:
        # Get total AR from ACDOCA mock
        ar = pd.read_sql("SELECT SUM(debit_amount_local) - SUM(credit_amount_local) as val FROM fct_gl_reconciliation WHERE gl_account='300001'", engine).iloc[0]['val']
        ar_val = ar if pd.notnull(ar) else 0
        st.metric("Total Accounts Receivable", f"₹{ar_val:,.2f}")
        
    st.subheader("Recent ACDOCA Postings")
    df_gl = pd.read_sql("SELECT gl_doc_number, posting_date, gl_account, debit_amount_local, credit_amount_local FROM fct_gl_reconciliation ORDER BY posting_date DESC LIMIT 10", engine)
    st.dataframe(df_gl)

elif persona == "Supply Chain":
    st.header("Supply Chain & Inventory (MM Module)")
    st.write("Inventory balances and fulfillment metrics.")
    st.metric("Avg Fulfillment Lead Time", f"{metrics.get_order_lead_time():.1f} days")
    
    st.subheader("Fulfillment Status")
    df_fill = pd.read_sql("SELECT is_fully_delivered, count(*) as count FROM fct_o2c_transactions GROUP BY is_fully_delivered", engine)
    st.bar_chart(df_fill.set_index('is_fully_delivered'))
