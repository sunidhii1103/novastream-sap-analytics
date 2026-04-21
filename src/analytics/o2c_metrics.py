import pandas as pd
from src.db.connection import get_engine

class O2CMetrics:
    def __init__(self):
        self.engine = get_engine()

    def get_order_lead_time(self):
        """Calculates Average Order Lead Time (Order to Delivery)."""
        df = pd.read_sql("""
            SELECT order_date, delivery_date 
            FROM fct_o2c_transactions 
            WHERE is_fully_delivered = 1
        """, self.engine)
        
        if df.empty:
            return 0
            
        df['order_date'] = pd.to_datetime(df['order_date'])
        df['delivery_date'] = pd.to_datetime(df['delivery_date'])
        df['lead_time_days'] = (df['delivery_date'] - df['order_date']).dt.days
        return df['lead_time_days'].mean()

    def get_perfect_order_rate(self):
        """Calculates Perfect Order Rate (delivered in full, billed in full)."""
        total = pd.read_sql("SELECT COUNT(*) as count FROM fct_o2c_transactions", self.engine).iloc[0]['count']
        if total == 0:
            return 0
            
        perfect = pd.read_sql("""
            SELECT COUNT(*) as count 
            FROM fct_o2c_transactions 
            WHERE is_fully_delivered = 1 AND is_fully_billed = 1
        """, self.engine).iloc[0]['count']
        
        return (perfect / total) * 100

    def get_revenue_leakage(self):
        """Calculates Revenue Leakage (Billed vs Received)."""
        # Simplified: Sum of invoices not paid after 30 days
        df = pd.read_sql("""
            SELECT sum(invoice_amount_local) as leakage 
            FROM fct_o2c_transactions 
            WHERE is_fully_billed = 1 AND is_fully_paid = 0
        """, self.engine)
        
        val = df.iloc[0]['leakage']
        return val if pd.notnull(val) else 0

if __name__ == "__main__":
    metrics = O2CMetrics()
    print(f"Avg Order Lead Time: {metrics.get_order_lead_time():.2f} days")
    print(f"Perfect Order Rate: {metrics.get_perfect_order_rate():.2f}%")
    print(f"Potential Revenue Leakage: INR {metrics.get_revenue_leakage():.2f}")
