import pandas as pd
from src.db.connection import get_engine

def validate_referential_integrity():
    """Validates data in the data warehouse."""
    engine = get_engine()
    
    print("Running ETL Validation...")
    try:
        # Check if all orders have valid customers
        invalid_customers = pd.read_sql("""
            SELECT o.order_id 
            FROM fct_o2c_transactions o
            LEFT JOIN dim_customer c ON o.customer_key = c.customer_key
            WHERE c.customer_key IS NULL
        """, engine)
        
        if not invalid_customers.empty:
            print(f"Validation Error: {len(invalid_customers)} orders have invalid customers.")
        else:
            print("Validation Passed: Customer referential integrity intact.")
            
        # Check if FI postings tie out to Invoices
        unmatched_fi = pd.read_sql("""
            SELECT f.gl_doc_number 
            FROM fct_gl_reconciliation f
            LEFT JOIN fct_o2c_transactions o ON f.source_document_number = o.invoice_id
            WHERE o.invoice_id IS NULL AND f.source_table_name = 'VBRK'
        """, engine)
        
        if not unmatched_fi.empty:
            print(f"Validation Error: {len(unmatched_fi)} FI postings have no matching invoice.")
        else:
            print("Validation Passed: FI to SD (Invoice) referential integrity intact.")
            
    except Exception as e:
        print(f"ETL Validation failed: {str(e)}")

if __name__ == "__main__":
    validate_referential_integrity()
