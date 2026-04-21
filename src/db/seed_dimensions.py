import pandas as pd
from sqlalchemy import text
from src.db.connection import get_engine
import sys
import os

# Add project root to python path to avoid import errors
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def seed_data():
    engine = get_engine()
    
    # 1. Seed Plants
    plants_data = [
        {"plant_id": "PL01", "plant_name": "NovaStream Main Plant", "city": "Bhubaneswar", "plant_type": "MANUFACTURING", "is_active": True},
        {"plant_id": "PL02", "plant_name": "NovaStream Distribution Hub", "city": "Pune", "plant_type": "DISTRIBUTION", "is_active": True}
    ]
    pd.DataFrame(plants_data).to_sql('dim_plant', engine, if_exists='append', index=False)

    # 2. Seed Customers
    customers_data = [
        {"customer_id": "C1001", "customer_name": "Apex Distributors", "customer_segment": "WHOLESALE", "city": "Delhi", "state": "DL", "is_current": True},
        {"customer_id": "C1002", "customer_name": "TechMart Pvt. Ltd.", "customer_segment": "WHOLESALE", "city": "Mumbai", "state": "MH", "is_current": True},
        {"customer_id": "C1003", "customer_name": "ElectroWorld Retail", "customer_segment": "RETAIL", "city": "Bangalore", "state": "KA", "is_current": True}
    ]
    pd.DataFrame(customers_data).to_sql('dim_customer', engine, if_exists='append', index=False)

    # 3. Seed Products
    products_data = [
        {"material_code": "NSTV-55", "material_description": "NovaStream SmartTV 55", "material_type": "FERT", "division_key": 1, "product_category": "SmartTV", "standard_cost_local": 22500.00, "is_current": True},
        {"material_code": "NASP-01", "material_description": "NovaStream Audio Sys Pro", "material_type": "FERT", "division_key": 1, "product_category": "AudioSystem", "standard_cost_local": 5000.00, "is_current": True}
    ]
    pd.DataFrame(products_data).to_sql('dim_product', engine, if_exists='append', index=False)

    # 4. Seed GL Accounts
    gl_accounts_data = [
        {"gl_account_code": "200001", "gl_account_description": "Finished Goods Inventory", "account_type": "ASSET", "account_category": "Inventory"},
        {"gl_account_code": "300001", "gl_account_description": "Accounts Receivable", "account_type": "ASSET", "account_category": "AR"},
        {"gl_account_code": "500001", "gl_account_description": "Bank Account", "account_type": "ASSET", "account_category": "Cash"},
        {"gl_account_code": "600001", "gl_account_description": "Revenue - Electronics Sales", "account_type": "REVENUE", "account_category": "Revenue-Sales"},
        {"gl_account_code": "700001", "gl_account_description": "Cost of Goods Sold", "account_type": "EXPENSE", "account_category": "COGS"},
        {"gl_account_code": "800001", "gl_account_description": "GST Output Tax Payable", "account_type": "LIABILITY", "account_category": "Tax"}
    ]
    pd.DataFrame(gl_accounts_data).to_sql('dim_gl_account', engine, if_exists='append', index=False)

    print("Dimensions seeded successfully.")

if __name__ == "__main__":
    seed_data()
