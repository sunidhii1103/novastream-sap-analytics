import pytest
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.db.connection import get_engine

def test_fi_balances_match_o2c():
    """Validates that total invoiced revenue matches total revenue posted to GL 600001."""
    engine = get_engine()
    
    # 1. Total Invoice Amount
    df_inv = pd.read_sql("SELECT SUM(invoice_amount_local) as total FROM fct_o2c_transactions WHERE is_fully_billed = 1", engine)
    total_invoiced = df_inv.iloc[0]['total']
    if pd.isnull(total_invoiced):
        total_invoiced = 0
        
    # 2. Total Revenue Credit (GL 600001)
    df_rev = pd.read_sql("SELECT SUM(credit_amount_local) as total FROM fct_gl_reconciliation WHERE gl_account = '600001'", engine)
    total_gl_revenue = df_rev.iloc[0]['total']
    if pd.isnull(total_gl_revenue):
        total_gl_revenue = 0
        
    # Total AR Debit (GL 300001)
    df_ar = pd.read_sql("SELECT SUM(debit_amount_local) as total FROM fct_gl_reconciliation WHERE gl_account = '300001'", engine)
    total_gl_ar = df_ar.iloc[0]['total']
    if pd.isnull(total_gl_ar):
        total_gl_ar = 0

    assert round(total_invoiced, 2) == round(total_gl_revenue, 2), "Invoiced amount does not match GL Revenue Credit!"
    assert round(total_invoiced, 2) == round(total_gl_ar, 2), "Invoiced amount does not match GL AR Debit!"
