# NovaStream Electronics SAP Analytics Pipeline

This project simulates an SAP S/4HANA Order-to-Cash (O2C) analytics pipeline locally, transforming synthetic transaction data into an OLAP Star Schema for NovaStream Electronics (Company Code NV01). It builds automated FI postings (ACDOCA) directly linked to O2C events and provides an interactive Streamlit dashboard for business reporting.

## Project Structure

- `src/db/`: Database connection and schema definitions, plus dimension seed scripts.
- `src/data_gen/`: Scripts generating simulated SAP transactions (Sales Orders, Deliveries, Invoices) and corresponding FI GL Postings.
- `src/etl/`: Validation logic for data warehousing.
- `src/analytics/`: Business logic metrics calculation (Lead times, fulfillment rate, revenue leakage).
- `src/dashboard/`: Interactive Streamlit dashboard with three Persona views.
- `tests/`: Automated validations (Pytest) checking FI to SD referential integrity and balance checks.

## Setup Instructions

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize Database**
   Initialize the SQLite data warehouse (`novastream_analytics.db`) and seed the dimension tables:
   ```bash
   python src/db/schema.py
   python src/db/seed_dimensions.py
   ```

3. **Generate Simulated Data**
   Run the following scripts in order to build the transaction facts and financial postings:
   ```bash
   python src/data_gen/sales_orders.py
   python src/data_gen/deliveries.py
   python src/data_gen/fi_postings.py
   ```

4. **Validate ETL Pipeline**
   Check that data and referential integrity between SD and FI modules is preserved:
   ```bash
   python src/etl/validate.py
   ```

5. **Run the Dashboard**
   Launch the Analytics Dashboard:
   ```bash
   streamlit run src/dashboard/app.py
   ```

6. **Run Tests**
   Validate financial balances using Pytest:
   ```bash
   pytest tests/
   ```

## Key SAP Validations Modeled
- **Referential Integrity**: Sales Orders to Customers & Plants.
- **O2C Fulfillment Flow**: VBAK/VBAP → LIKP/LIPS → VBRK/VBRP.
- **FI Auto-Postings (ACDOCA)**: Invoice generation automatically triggers AR Debit (300001) and Revenue Credit (600001) for Company Code `NV01`.
