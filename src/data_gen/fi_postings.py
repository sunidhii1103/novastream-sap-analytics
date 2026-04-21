import pandas as pd
from src.db.connection import get_engine

def generate_fi_postings():
    """Generates ACDOCA postings for invoices (Accounts Receivable and Revenue)."""
    engine = get_engine()
    
    # Find billed transactions that don't have FI postings
    # Simplification: just process all fully billed that aren't marked or we just process all for MVP.
    invoices_df = pd.read_sql("""
        SELECT * FROM fct_o2c_transactions 
        WHERE is_fully_billed = 1 AND invoice_id NOT IN (
            SELECT source_document_number FROM fct_gl_reconciliation
        )
    """, engine)
    
    if invoices_df.empty:
        print("No new invoices for FI posting.")
        return
        
    gl_entries = []
    
    for _, row in invoices_df.iterrows():
        inv_id = row['invoice_id']
        date = row['invoice_date']
        amt = row['invoice_amount_local']
        
        # 1. Debit Accounts Receivable (300001)
        gl_entries.append({
            'gl_doc_number': f"FI-{inv_id}",
            'posting_date': date,
            'gl_account': '300001',
            'debit_amount_local': amt,
            'credit_amount_local': 0,
            'source_document_number': inv_id,
            'source_table_name': 'VBRK',
            'reconciliation_status': 'MATCHED'
        })
        
        # 2. Credit Revenue (600001)
        gl_entries.append({
            'gl_doc_number': f"FI-{inv_id}",
            'posting_date': date,
            'gl_account': '600001',
            'debit_amount_local': 0,
            'credit_amount_local': amt,
            'source_document_number': inv_id,
            'source_table_name': 'VBRK',
            'reconciliation_status': 'MATCHED'
        })
        
    df = pd.DataFrame(gl_entries)
    df.to_sql('fct_gl_reconciliation', engine, if_exists='append', index=False)
    print(f"Generated {len(gl_entries)} FI postings for NV01.")

if __name__ == "__main__":
    generate_fi_postings()
