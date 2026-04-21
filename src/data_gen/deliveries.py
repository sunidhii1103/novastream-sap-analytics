import pandas as pd
from datetime import timedelta
from src.db.connection import get_engine

def generate_deliveries_and_invoices():
    """Simulate fulfillment and billing for existing sales orders."""
    engine = get_engine()
    
    # Load unfulfilled orders
    orders_df = pd.read_sql("SELECT * FROM fct_o2c_transactions WHERE is_fully_delivered = 0", engine)
    
    if orders_df.empty:
        print("No pending orders to deliver.")
        return
        
    # Simulate delivery and invoice creation
    updates = []
    for _, row in orders_df.iterrows():
        # Delivery 1-3 days after order
        delivery_date = pd.to_datetime(row['order_date']) + timedelta(days=1)
        invoice_date = delivery_date + timedelta(days=1)
        
        # SQL update string
        update_query = f"""
            UPDATE fct_o2c_transactions
            SET delivery_id = 'DEL-{row['order_id']}',
                delivery_date = '{delivery_date.date()}',
                delivery_qty = {row['order_qty']},
                is_fully_delivered = 1,
                invoice_id = 'INV-{row['order_id']}',
                invoice_date = '{invoice_date.date()}',
                invoice_amount_local = {row['order_amount_local']},
                is_fully_billed = 1
            WHERE o2c_fact_id = {row['o2c_fact_id']}
        """
        updates.append(update_query)
        
    with engine.begin() as conn:
        for q in updates:
            conn.exec_driver_sql(q)
            
    print(f"Processed deliveries and invoices for {len(updates)} orders.")

if __name__ == "__main__":
    generate_deliveries_and_invoices()
