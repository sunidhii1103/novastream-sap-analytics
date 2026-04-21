import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import random

# 1. Connect to your local SAP Simulation Database
conn = sqlite3.connect('novastream_sap.db')
cursor = conn.cursor()

# Ensure tables exist (Added to avoid 'no such table' errors on first run)
cursor.execute('''CREATE TABLE IF NOT EXISTS NOV_MARC (MATNR TEXT, WERKS TEXT, STLOC TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS NOV_SKB1 (SAKNR TEXT, BUKRS TEXT, TXT20 TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS NOV_VBAK (VBELN TEXT, ERDAT TEXT, BUKRS TEXT, VKORG TEXT, NETWR REAL, WERKS TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS NOV_ACDOCA (BELNR TEXT, GJAHR TEXT, BUKRS TEXT, RACCT TEXT, HSL REAL)''')

def seed_master_data():
    # Insert Company Code & Plants
    cursor.execute("INSERT OR REPLACE INTO NOV_MARC (MATNR, WERKS, STLOC) VALUES ('NSTV-55', 'PL01', 'SL01')")
    cursor.execute("INSERT OR REPLACE INTO NOV_MARC (MATNR, WERKS, STLOC) VALUES ('NSTV-55', 'PL02', 'SL01')")
    
    # Insert G/L Accounts (FI)
    gl_accounts = [
        ('600001', 'Sales Revenue'),
        ('700001', 'Cost of Goods Sold'),
        ('800001', 'GST Output Tax'),
        ('200001', 'Inventory Asset')
    ]
    for code, name in gl_accounts:
        cursor.execute("INSERT OR REPLACE INTO NOV_SKB1 (SAKNR, BUKRS, TXT20) VALUES (?, 'NV01', ?)", (code, name))

def simulate_o2c_transactions():
    # Simulate 20 Sales Orders and Financial Postings
    for i in range(1, 21):
        order_id = f"SO-{1000 + i}"
        plant = random.choice(['PL01', 'PL02'])
        revenue = random.randint(45000, 55000)
        tax = revenue * 0.18 # 18% GST as per your report
        
        # Insert Sales Record (SD)
        cursor.execute("""
            INSERT INTO NOV_VBAK (VBELN, ERDAT, BUKRS, VKORG, NETWR, WERKS) 
            VALUES (?, ?, 'NV01', 'NV10', ?, ?)
        """, (order_id, datetime.now().strftime('%Y-%m-%d'), revenue, plant))
        
        # Insert Financial Posting (FI - ACDOCA)
        # Credit Revenue, Debit Tax, etc.
        cursor.execute("""
            INSERT INTO NOV_ACDOCA (BELNR, GJAHR, BUKRS, RACCT, HSL) 
            VALUES (?, '2026', 'NV01', '600001', ?)
        """, (f"FI-{5000+i}", -revenue)) # Revenue is Credit
        
        cursor.execute("""
            INSERT INTO NOV_ACDOCA (BELNR, GJAHR, BUKRS, RACCT, HSL) 
            VALUES (?, '2026', 'NV01', '800001', ?)
        """, (f"FI-{5000+i}", -tax)) # Tax is Credit

    conn.commit()
    print("✅ Success: 20 NovaStream O2C Transactions injected!")

seed_master_data()
simulate_o2c_transactions()
conn.close()
