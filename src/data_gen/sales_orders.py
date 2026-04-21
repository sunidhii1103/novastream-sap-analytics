import pandas as pd
from datetime import datetime, timedelta
import random
from src.db.connection import get_engine
import uuid

def generate_sales_orders(num_orders=10):
    """Generate fake sales orders and insert them."""
    engine = get_engine()
    
    # Get dimensions
    customers = pd.read_sql("SELECT * FROM dim_customer", engine)
    products = pd.read_sql("SELECT * FROM dim_product", engine)
    plants = pd.read_sql("SELECT * FROM dim_plant", engine)
    
    if customers.empty or products.empty or plants.empty:
        print("Dimensions must be seeded first.")
        return

    orders_data = []
    
    start_date = datetime.now() - timedelta(days=30)
    
    for i in range(num_orders):
        order_date = start_date + timedelta(days=random.randint(0, 30))
        customer = customers.sample(1).iloc[0]
        product = products.sample(1).iloc[0]
        plant = plants.sample(1).iloc[0]
        
        qty = random.randint(1, 50)
        price = qty * product['standard_cost_local'] * 1.4 # 40% margin
        
        order_id = f"SO-{1000 + i}"
        
        orders_data.append({
            'order_date': order_date.date(),
            'order_id': order_id,
            'order_item_id': "10",
            'order_amount_local': price,
            'order_qty': qty,
            'customer_key': int(customer['customer_key']),
            'product_key': int(product['product_key']),
            'plant_key': int(plant['plant_key']),
            'is_fully_delivered': False,
            'is_fully_billed': False,
            'is_fully_paid': False
        })
        
    df = pd.DataFrame(orders_data)
    df.to_sql('fct_o2c_transactions', engine, if_exists='append', index=False)
    print(f"Generated {num_orders} sales orders.")
    return df

if __name__ == "__main__":
    generate_sales_orders()
