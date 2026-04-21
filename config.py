import os

# SAP NovaStream Electronics Constants
COMPANY_CODE = "NV01"
SALES_ORG = "NV10"
PLANTS = ["PL01", "PL02"]
DIST_CHANNELS = ["10", "20"]
DIVISIONS = ["EL", "AC"]
CURRENCY = "INR"

# Database path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
DB_PATH = f"sqlite:///{os.path.join(DATA_DIR, 'novastream_analytics.db')}"
