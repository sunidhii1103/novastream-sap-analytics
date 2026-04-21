# Data Schema & Software Requirements Specification (SRS)
## NovaStream Electronics SAP Analytics Data Model

**Project:** NovaStream Electronics Data Analytics Platform  
**Version:** 1.0  
**Date:** April 21, 2026  
**Technical Owner:** Lead Data Engineer  

---

## 1. Technology Stack

### 1.1 Data Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│  Presentation Layer (Streamlit Web Dashboard)          │
│  - Sales Manager Dashboard (Revenue, O2C Pipeline)      │
│  - Finance Controller Dashboard (GL, Close Automation)  │
│  - Supply Chain Dashboard (Inventory, Turnover)         │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│  Analytical Layer (Business Logic, Aggregations)        │
│  - O2C Fact Table Aggregations                          │
│  - GL Reconciliation Rules Engine                       │
│  - Profitability Calculations                           │
│  - KPI Computations (DSO, Inventory Turnover, etc.)    │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│  Data Warehouse Layer (SQLite → PostgreSQL → HANA*)     │
│  - Star Schema (Facts & Dimensions)                     │
│  - Staging Layer (raw data from ETL)                    │
│  - Conformed Dimensions (reusable across all models)    │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│  ETL Layer (Python - Pandas, SQLAlchemy)                │
│  - Extraction (SAP table extraction scripts)            │
│  - Transformation (business logic, joins, aggregations) │
│  - Loading (to DW, error handling, auditing)            │
│  - Scheduling (cron/Airflow orchestration)              │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│  Source Layer (SAP ERP - FI, MM, SD Modules)            │
│  - Company Code NV01 (Financial Accounting)             │
│  - Plants PL01, PL02 (Materials Management)             │
│  - Sales Org NV10 (Sales & Distribution)                │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Technology Components

| Layer | Technology | Purpose | Notes |
|-------|-----------|---------|-------|
| **Extraction** | SAP RFC / SQL Query | Read from SAP tables (VBAK, ACDOCA, MSEG, etc.) | RFC preferred for live; SQL for batch testing |
| **ETL Orchestration** | Apache Airflow (or cron + Python) | Schedule daily extract, transform, load jobs | Airflow for enterprise; cron for MVP |
| **Data Processing** | Python 3.10+ with Pandas, NumPy, SQLAlchemy | Transform, aggregate, calculate KPIs | Pandas for in-memory aggregations; SQLAlchemy for DB abstraction |
| **Data Warehouse** | SQLite (dev/test) → PostgreSQL (production) → SAP HANA* | Store conformed data, history, aggregates | SQLite for prototyping; PostgreSQL for multi-user; HANA for enterprise |
| **Presentation** | Streamlit Framework | Interactive dashboards for three personas | Python-native; rapid prototyping; real-time data binding |
| **Visualization Libraries** | Plotly, Altair, Matplotlib | Charts, heatmaps, KPI cards | Plotly for interactive exploration |
| **Version Control** | Git / GitHub | Code repository and documentation | Standard practice |
| **Documentation** | Markdown + Confluence | Data dictionary, transformation logic, SLAs | Version all metadata |

---

## 2. Data Model Architecture (Star Schema)

### 2.1 Conceptual Overview

The analytics platform uses a **Star Schema** design optimized for OLAP (Online Analytical Processing):
- **Fact Tables:** Transaction-level events (sales orders, deliveries, invoices, payments)
- **Dimension Tables:** Reference entities (customers, products, plants, GL accounts, time periods)
- **Conformed Dimensions:** Reusable across all fact tables (Date, Plant, Customer, Product)

### 2.2 Fact Tables

#### Fact Table 1: O2C_FACTS (Order-to-Cash Transaction Facts)

Stores one row per sales order item, enriched with fulfillment and billing status.

**Physical Table Name:** `fct_o2c_transactions`  
**Granularity:** One row per VBAP (Sales Order Item)  
**Volume:** ~500–1,000 rows/day (estimated)

| Column Name | Data Type | Source SAP Table | Description | Example |
|-------------|-----------|------------------|-------------|---------|
| **o2c_fact_id** | BIGINT PK | Generated | Unique surrogate key | 1001 |
| **order_date** | DATE | VBAK.ERDAT | Date sales order created | 2026-04-15 |
| **order_id** | VARCHAR(20) | VBAK.VBELN | Sales order number (NOT unique per row; multiple items per order) | 0013456789 |
| **order_item_id** | VARCHAR(20) | VBAP.POSNR | Line item number (NV01-VBELN-POSNR = unique) | 10 |
| **order_amount_local** | DECIMAL(15,2) | VBAP.NETWR | Net order value in INR (excl. GST) | 900000.00 |
| **order_qty** | DECIMAL(13,3) | VBAP.MENGE | Quantity ordered | 20.000 |
| **delivery_id** | VARCHAR(20) | LIKP.VBELN | Linked delivery document (NULL if not yet delivered) | 0008765432 |
| **delivery_date** | DATE | LIKP.WBSTK | Goods issue posting date (NULL if pending) | 2026-04-16 |
| **delivery_qty** | DECIMAL(13,3) | LIPS.LFIMG | Quantity delivered (may be partial) | 20.000 |
| **invoice_id** | VARCHAR(20) | VBRK.VBRK# | Billing document number (NULL if not billed) | 0000234561 |
| **invoice_date** | DATE | VBRK.FKDAT | Billing document date (NULL if pending) | 2026-04-17 |
| **invoice_amount_local** | DECIMAL(15,2) | VBRP.NETWR | Invoiced net amount (may differ from order if partial) | 900000.00 |
| **gst_amount** | DECIMAL(15,2) | ACDOCA (800001) | GST payable posted to GL 800001 | 162000.00 |
| **invoice_qty** | DECIMAL(13,3) | VBRP.FKIMG | Quantity billed (may be partial) | 20.000 |
| **cogs_posted_amount** | DECIMAL(15,2) | ACDOCA (700001) | COGS posted to GL 700001 at goods issue | 450000.00 |
| **cash_received_date** | DATE | BSAK.CLEARING_DATE | Date payment cleared invoice (NULL if unpaid) | 2026-05-05 |
| **cash_received_amount** | DECIMAL(15,2) | BSAK.DMBTR | Payment amount applied (may be partial) | 1062000.00 |
| **is_fully_delivered** | BOOLEAN | Logic | TRUE if delivery_qty = order_qty | TRUE |
| **is_fully_billed** | BOOLEAN | Logic | TRUE if invoice_qty = order_qty | TRUE |
| **is_fully_paid** | BOOLEAN | Logic | TRUE if cash_received_amount ≥ invoice_amount | TRUE |
| **days_to_delivery** | INT | Logic | delivery_date - order_date (NULL if pending) | 1 |
| **days_to_invoice** | INT | Logic | invoice_date - order_date (NULL if pending) | 2 |
| **days_to_cash** | INT | Logic | cash_received_date - invoice_date (NULL if unpaid) | 18 |
| **o2c_cycle_days** | INT | Logic | cash_received_date - order_date (NULL if incomplete) | 20 |
| **customer_key** | INT FK | DIM_CUSTOMER | Foreign key to customer dimension | 102 |
| **product_key** | INT FK | DIM_PRODUCT | Foreign key to product dimension | 305 |
| **plant_key** | INT FK | DIM_PLANT | Foreign key to plant dimension | 1 |
| **sales_org_key** | INT FK | DIM_SALES_ORG | Foreign key to sales org dimension | 1 |
| **dist_channel_key** | INT FK | DIM_DIST_CHANNEL | Foreign key to distribution channel | 1 |
| **division_key** | INT FK | DIM_DIVISION | Foreign key to division dimension | 1 |
| **sales_area_key** | INT FK | DIM_SALES_AREA | Foreign key to sales area (SOrg/Channel/Division) | 1 |
| **company_code_key** | INT FK | DIM_COMPANY_CODE | Foreign key to company code (NV01) | 1 |
| **date_key_order** | INT FK | DIM_DATE | Foreign key to date dimension (order date) | 20260415 |
| **date_key_delivery** | INT FK | DIM_DATE | Foreign key to date dimension (delivery date) | 20260416 |
| **date_key_invoice** | INT FK | DIM_DATE | Foreign key to date dimension (invoice date) | 20260417 |
| **date_key_cash** | INT FK | DIM_DATE | Foreign key to date dimension (cash date) | 20260505 |
| **etl_load_date** | TIMESTAMP | System | When row was loaded into DW | 2026-04-18 10:30:45 |
| **etl_update_date** | TIMESTAMP | System | Last update to row (tracks SCD Type 2 changes) | 2026-04-18 10:30:45 |
| **is_current** | BOOLEAN | System | SCD Type 2 current flag | TRUE |

**Indexes:**
```sql
CREATE INDEX idx_o2c_order_date ON fct_o2c_transactions(date_key_order);
CREATE INDEX idx_o2c_customer ON fct_o2c_transactions(customer_key);
CREATE INDEX idx_o2c_product ON fct_o2c_transactions(product_key);
CREATE INDEX idx_o2c_invoice_date ON fct_o2c_transactions(date_key_invoice);
CREATE INDEX idx_o2c_is_paid ON fct_o2c_transactions(is_fully_paid);
```

---

#### Fact Table 2: GL_RECONCILIATION_FACTS (General Ledger & Source Matching)

Stores one row per GL posting with lineage back to source document.

**Physical Table Name:** `fct_gl_reconciliation`  
**Granularity:** One row per ACDOCA line item  
**Volume:** ~2,000–5,000 rows/day

| Column Name | Data Type | Source | Description | Example |
|-------------|-----------|--------|-------------|---------|
| **gl_fact_id** | BIGINT PK | Generated | Unique key | 5001 |
| **gl_doc_number** | VARCHAR(20) | ACDOCA.BELNR | GL document number | 0000345678 |
| **gl_item_number** | VARCHAR(5) | ACDOCA.BUZEI | Line item within GL doc | 01 |
| **posting_date** | DATE | ACDOCA.BUDAT | GL posting date | 2026-04-17 |
| **gl_account** | VARCHAR(10) | ACDOCA.GKONT | GL account (e.g., 600001, 700001, 800001) | 600001 |
| **gl_account_name** | VARCHAR(100) | Chart of Accounts Master | GL account description | Revenue - Electronics Sales |
| **debit_amount_local** | DECIMAL(15,2) | ACDOCA.DMBTR (if Dr) | Debit in INR | 1062000.00 |
| **credit_amount_local** | DECIMAL(15,2) | ACDOCA.DMBTR (if Cr) | Credit in INR | 0.00 |
| **source_document_type** | VARCHAR(20) | Logic | Type of source doc (SD, MM, FI_MANUAL) | SD |
| **source_document_number** | VARCHAR(20) | ACDOCA.XBLNR / VBELN / MKPF | Original business doc (invoice, GRN, etc.) | 0000234561 |
| **source_document_item** | VARCHAR(10) | Logic | Item within source doc | 01 |
| **source_table_name** | VARCHAR(30) | Logic | SAP table source (VBRK, MSEG, etc.) | VBRK |
| **reference_order_number** | VARCHAR(20) | Logic | Related sales/PO number | 0013456789 |
| **customer_key** | INT FK | DIM_CUSTOMER | Customer (if applicable) | 102 |
| **product_key** | INT FK | DIM_PRODUCT | Product (if applicable) | 305 |
| **plant_key** | INT FK | DIM_PLANT | Plant (if applicable) | 1 |
| **company_code_key** | INT FK | DIM_COMPANY_CODE | Company Code NV01 | 1 |
| **date_key** | INT FK | DIM_DATE | Posting date key | 20260417 |
| **reconciliation_status** | VARCHAR(20) | Logic | MATCHED, UNMATCHED, VARIANCE_FLAG | MATCHED |
| **variance_amount** | DECIMAL(15,2) | Logic | Difference from expected (0 if matched) | 0.00 |
| **reconciliation_note** | VARCHAR(500) | Manual | Explanation of any variance or hold | NULL |
| **etl_load_date** | TIMESTAMP | System | Load timestamp | 2026-04-18 10:30:45 |

**Indexes:**
```sql
CREATE INDEX idx_gl_posting_date ON fct_gl_reconciliation(date_key);
CREATE INDEX idx_gl_account ON fct_gl_reconciliation(gl_account);
CREATE INDEX idx_gl_source_doc ON fct_gl_reconciliation(source_document_number);
CREATE INDEX idx_gl_recon_status ON fct_gl_reconciliation(reconciliation_status);
```

---

#### Fact Table 3: INVENTORY_FACTS (Material Stock Movements & Balances)

Stores one row per material per plant per storage location per day (daily snapshot).

**Physical Table Name:** `fct_inventory_facts`  
**Granularity:** One row per MATNR-WERKS-LGORT per day  
**Volume:** ~500 rows/day (8 materials × 2 plants × 5 storage locations ≈ 80 locations, but only active ones)

| Column Name | Data Type | Source | Description | Example |
|-------------|-----------|--------|-------------|---------|
| **inv_fact_id** | BIGINT PK | Generated | Unique key | 7001 |
| **snapshot_date** | DATE | MSEG.BUDAT | Date of inventory snapshot (daily EOD) | 2026-04-18 |
| **material_key** | INT FK | DIM_PRODUCT | Foreign key to product | 305 |
| **plant_key** | INT FK | DIM_PLANT | Foreign key to plant | 1 |
| **storage_location_code** | VARCHAR(10) | MSEG.LGORT | Storage location (SL01–SL05) | SL03 |
| **storage_location_name** | VARCHAR(100) | Master Data | Storage location description | Finished Goods Store - PL01 |
| **opening_balance_qty** | DECIMAL(13,3) | Prior day balance | Opening stock quantity | 120.000 |
| **receipts_qty** | DECIMAL(13,3) | MSEG (GRN/production) | Quantity received during day | 50.000 |
| **issues_qty** | DECIMAL(13,3) | MSEG (goods issue) | Quantity issued during day | 20.000 |
| **closing_balance_qty** | DECIMAL(13,3) | Logic | Closing stock = opening + receipts − issues | 150.000 |
| **standard_cost_per_unit** | DECIMAL(13,4) | MARA.STPRS | Standard cost/unit from material master | 22500.0000 |
| **inventory_value_local** | DECIMAL(15,2) | Logic | closing_balance_qty × standard_cost | 3375000.00 |
| **days_on_hand** | INT | Logic | Closing balance / avg daily demand (from O2C facts) | 45 |
| **is_safety_stock_adequate** | BOOLEAN | Logic | closing_balance_qty ≥ safety_stock_threshold | TRUE |
| **is_obsolete** | BOOLEAN | Logic | days_on_hand > 180 days AND zero_sales_180d | FALSE |
| **date_key** | INT FK | DIM_DATE | Snapshot date key | 20260418 |
| **etl_load_date** | TIMESTAMP | System | Load timestamp | 2026-04-18 22:15:30 |

**Indexes:**
```sql
CREATE INDEX idx_inv_snapshot_date ON fct_inventory_facts(date_key);
CREATE INDEX idx_inv_material ON fct_inventory_facts(material_key);
CREATE INDEX idx_inv_plant ON fct_inventory_facts(plant_key);
CREATE INDEX idx_inv_obsolete ON fct_inventory_facts(is_obsolete);
```

---

### 2.3 Dimension Tables (Conformed)

#### DIM_CUSTOMER (Customer Master)

| Column | Type | Source | Notes |
|--------|------|--------|-------|
| customer_key | INT PK | Generated | Surrogate key |
| customer_id | VARCHAR(20) | KNA1.KUNNR | SAP customer number (e.g., C1001) |
| customer_name | VARCHAR(100) | KNA1.NAME1 | Full legal name |
| customer_segment | VARCHAR(20) | Business Logic | WHOLESALE or RETAIL (based on dist channel) |
| city | VARCHAR(50) | KNA1.CITY | City (Delhi, Mumbai, Bangalore) |
| state | VARCHAR(20) | KNA1.REGION | State/Region (derived) |
| gstin | VARCHAR(20) | KNA1.TCODE | GST registration number |
| credit_limit_local | DECIMAL(15,2) | KNA1.KURVR | Customer credit limit |
| default_delivery_plant | VARCHAR(10) | KNA1 / Logic | Plant used for delivery (PL01 or PL02) |
| effective_from_date | DATE | KNA1.CREATED_DATE | Customer creation date |
| effective_to_date | DATE | SCD Type 2 | NULL if current, date if historical |
| is_current | BOOLEAN | SCD Type 2 | TRUE for current record |
| etl_load_date | TIMESTAMP | System | Load timestamp |

**Sample Rows:**
```
customer_key | customer_id | customer_name              | customer_segment | city      | state | is_current
1            | C1001       | Apex Distributors          | WHOLESALE        | Delhi     | DL    | TRUE
2            | C1002       | TechMart Pvt. Ltd.         | WHOLESALE        | Mumbai    | MH    | TRUE
3            | C1003       | ElectroWorld Retail        | RETAIL           | Bangalore | KA    | TRUE
```

---

#### DIM_PRODUCT (Material Master)

| Column | Type | Source | Notes |
|--------|------|--------|-------|
| product_key | INT PK | Generated | Surrogate key |
| material_code | VARCHAR(20) | MARA.MATNR | Material number (e.g., NSTV-55) |
| material_description | VARCHAR(100) | MARA.MAKTX | Material description |
| material_type | VARCHAR(10) | MARA.MTART | FERT (finished), ROH (raw), HAWA (trading) |
| division_key | INT FK | DIM_DIVISION | Division (EL/AC) |
| product_category | VARCHAR(30) | Business Logic | SmartTV, AudioSystem, Remote, Cable, PCB, Panel |
| unit_of_measure | VARCHAR(5) | MARA.MEINS | UOM (EA, PC, KG, etc.) |
| standard_cost_local | DECIMAL(13,4) | MARA.STPRS | Standard cost in INR |
| planned_selling_price_local | DECIMAL(13,2) | Material Master (Sales view) | List price in INR |
| product_line | VARCHAR(20) | Hierarchy | Consumer Electronics, Components |
| effective_from_date | DATE | MARA.CREATED_DATE | Creation date |
| is_current | BOOLEAN | SCD Type 2 | TRUE if current |
| etl_load_date | TIMESTAMP | System | Load timestamp |

**Sample Rows:**
```
product_key | material_code | material_description | material_type | division_key | product_category
301         | NSTV-55       | NovaStream SmartTV 55" | FERT          | 1 (EL)      | SmartTV
302         | NASP-01       | NovaStream Audio Sys Pro | FERT          | 1 (EL)      | AudioSystem
303         | RM-PCB-01     | Printed Circuit Board | ROH           | NULL         | Components
```

---

#### DIM_PLANT (Plant Master)

| Column | Type | Source | Notes |
|--------|------|--------|-------|
| plant_key | INT PK | Generated | Surrogate key |
| plant_id | VARCHAR(10) | MARC.WERKS | Plant code (PL01, PL02) |
| plant_name | VARCHAR(50) | Plant Master | Plant description |
| city | VARCHAR(50) | Plant Master | City (Bhubaneswar, Pune) |
| state | VARCHAR(20) | Plant Master | State (Odisha, Maharashtra) |
| plant_type | VARCHAR(20) | Master Data | MANUFACTURING, DISTRIBUTION |
| company_code_key | INT FK | DIM_COMPANY_CODE | Parent company (NV01) |
| plant_storage_locations | VARCHAR(200) | Metadata | Comma-separated SL codes (SL01,SL02,SL03) |
| effective_from_date | DATE | Plant creation date | Creation date |
| is_active | BOOLEAN | Master Data | TRUE if operational |
| etl_load_date | TIMESTAMP | System | Load timestamp |

**Sample Rows:**
```
plant_key | plant_id | plant_name                | city           | plant_type     | is_active
1         | PL01     | NovaStream Main Plant     | Bhubaneswar    | MANUFACTURING  | TRUE
2         | PL02     | NovaStream Distribution Hub | Pune          | DISTRIBUTION   | TRUE
```

---

#### DIM_GL_ACCOUNT (Chart of Accounts)

| Column | Type | Source | Notes |
|--------|------|--------|-------|
| gl_account_key | INT PK | Generated | Surrogate key |
| gl_account_code | VARCHAR(10) | ACDOCA.GKONT | GL account number |
| gl_account_description | VARCHAR(100) | Chart of Accounts | Account description |
| account_type | VARCHAR(20) | Master Data | REVENUE, EXPENSE, ASSET, LIABILITY, EQUITY |
| account_category | VARCHAR(50) | Master Data | Revenue-Sales, COGS, Inventory, AR, Payables, Tax |
| module_source | VARCHAR(10) | Master Data | FI, MM, SD |
| is_balance_sheet | BOOLEAN | Master Data | TRUE if BS account, FALSE if P&L |
| company_code_key | INT FK | DIM_COMPANY_CODE | Company code (NV01) |
| etl_load_date | TIMESTAMP | System | Load timestamp |

**Sample Rows:**
```
gl_account_key | gl_account_code | gl_account_description | account_type | account_category
1              | 200001          | Finished Goods Inventory | ASSET        | Inventory
2              | 300001          | Accounts Receivable    | ASSET        | AR
3              | 500001          | Bank Account           | ASSET        | Cash
4              | 600001          | Revenue - Electronics Sales | REVENUE   | Revenue-Sales
5              | 600002          | Revenue - Accessories Sales | REVENUE   | Revenue-Sales
6              | 700001          | Cost of Goods Sold     | EXPENSE      | COGS
7              | 800001          | GST Output Tax Payable | LIABILITY    | Tax
```

---

#### DIM_SALES_ORG (Sales Organization)

| Column | Type | Source | Notes |
|--------|------|--------|-------|
| sales_org_key | INT PK | Generated | Surrogate key |
| sales_org_id | VARCHAR(10) | SD Master | Sales Org code (NV10) |
| sales_org_name | VARCHAR(50) | SD Master | Sales Org description |
| company_code_key | INT FK | DIM_COMPANY_CODE | Parent company (NV01) |
| currency | VARCHAR(3) | SD Master | Currency (INR for NovaStream) |
| etl_load_date | TIMESTAMP | System | Load timestamp |

---

#### DIM_DIST_CHANNEL (Distribution Channel)

| Column | Type | Source | Notes |
|--------|------|--------|-------|
| dist_channel_key | INT PK | Generated | Surrogate key |
| dist_channel_id | VARCHAR(2) | SD Master | Channel code (10, 20) |
| dist_channel_name | VARCHAR(30) | SD Master | Channel name (Wholesale, Retail) |
| sales_org_key | INT FK | DIM_SALES_ORG | Parent sales org |
| etl_load_date | TIMESTAMP | System | Load timestamp |

---

#### DIM_DIVISION (Division)

| Column | Type | Source | Notes |
|--------|------|--------|-------|
| division_key | INT PK | Generated | Surrogate key |
| division_id | VARCHAR(2) | SD Master | Division code (EL, AC) |
| division_name | VARCHAR(30) | SD Master | Division name (Electronics, Accessories) |
| sales_org_key | INT FK | DIM_SALES_ORG | Parent sales org |
| etl_load_date | TIMESTAMP | System | Load timestamp |

---

#### DIM_SALES_AREA (Sales Area)

**Note:** Sales Area is a dimensional viewpoint combining Sales Org + Distribution Channel + Division.

| Column | Type | Source | Notes |
|--------|------|--------|-------|
| sales_area_key | INT PK | Generated | Surrogate key |
| sales_org_key | INT FK | DIM_SALES_ORG | Sales org (NV10) |
| dist_channel_key | INT FK | DIM_DIST_CHANNEL | Distribution channel |
| division_key | INT FK | DIM_DIVISION | Division |
| sales_area_code | VARCHAR(20) | Composite | NV10-10-EL format |
| sales_area_name | VARCHAR(100) | Composite | "NV10 Wholesale Electronics" |
| etl_load_date | TIMESTAMP | System | Load timestamp |

---

#### DIM_COMPANY_CODE (Company Code / Legal Entity)

| Column | Type | Source | Notes |
|--------|------|--------|-------|
| company_code_key | INT PK | Generated | Surrogate key |
| company_code_id | VARCHAR(10) | FI Master | Company code (NV01) |
| company_name | VARCHAR(100) | FI Master | Full legal name |
| country | VARCHAR(2) | FI Master | Country code (IN) |
| currency | VARCHAR(3) | FI Master | Functional currency (INR) |
| chart_of_accounts_id | VARCHAR(10) | FI Master | Chart of accounts (NVCA) |
| fiscal_year_variant | VARCHAR(10) | FI Master | Fiscal year (V3: April–March) |
| etl_load_date | TIMESTAMP | System | Load timestamp |

---

#### DIM_DATE (Time Dimension)

**Purpose:** Standard date dimension enabling all time-based analysis (by day, week, month, quarter, year).

| Column | Type | Example | Notes |
|--------|------|---------|-------|
| date_key | INT PK | 20260415 | YYYYMMDD format |
| calendar_date | DATE | 2026-04-15 | Actual date |
| day_of_month | INT | 15 | 1–31 |
| day_of_week | INT | 3 | 1=Monday, 7=Sunday |
| day_of_week_name | VARCHAR(10) | Wednesday | |
| week_of_year | INT | 16 | ISO week number |
| month_of_year | INT | 4 | 1–12 |
| month_name | VARCHAR(20) | April | Full month name |
| quarter_of_year | INT | 1 | Q1–Q4 (Apr–Jun=Q1 for Indian FY) |
| year_calendar | INT | 2026 | Calendar year |
| fiscal_year | INT | 2026 | Fiscal year (April–March, so Apr 2026 = FY 2026) |
| is_weekday | BOOLEAN | TRUE | TRUE if Mon–Fri |
| is_month_end | BOOLEAN | FALSE | TRUE if last day of month |
| is_quarter_end | BOOLEAN | FALSE | TRUE if last day of quarter |
| is_fiscal_year_end | BOOLEAN | FALSE | TRUE if March 31 |
| etl_load_date | TIMESTAMP | | Load timestamp |

---

## 3. ETL Transformation Logic

### 3.1 Extract Phase

**Source:** SAP ERP (FI, MM, SD modules)  
**Frequency:** Daily (e.g., 02:00 AM IST after EOD batch jobs)  
**Method:** RFC extraction or SQL direct query (depending on SAP connectivity)

**Extract Queries:**

```sql
-- Extract Sales Orders (VBAK/VBAP)
SELECT 
  vbak.vbeln, vbak.erdat, vbak.netwr,
  vbap.posnr, vbap.matnr, vbap.menge, vbap.werks
FROM vbak
INNER JOIN vbap ON vbak.vbeln = vbap.vbeln
WHERE vbak.bukrs = 'NV01'  -- Company Code
  AND vbak.erdat >= CURRENT_DATE - 1;  -- Last 24 hours

-- Extract GL Documents (ACDOCA)
SELECT 
  belnr, buzei, budat, gkont, dmbtr, bukrs
FROM acdoca
WHERE bukrs = 'NV01'
  AND budat >= CURRENT_DATE - 1;

-- Extract Material Documents (MSEG)
SELECT 
  mkpf, mseg.posnr, matnr, menge, werks, lgort, budat
FROM mseg
INNER JOIN mkpf ON mseg.mkpf = mkpf.mkpf
WHERE mkpf.bukrs = 'NV01'
  AND mkpf.budat >= CURRENT_DATE - 1;
```

---

### 3.2 Transform Phase

**Key Transformation Rules:**

#### Rule 1: O2C Linking (Fact Table O2C_FACTS)

**Logic:** For each VBAP, find associated LIKP, VBRK, and BSAK documents using sales order reference.

```python
# Pseudocode
def build_o2c_fact(vbap_row):
    order_id = vbap_row['vbeln']
    order_item = vbap_row['posnr']
    
    # Find delivery (LIKP → LIPS)
    delivery = likp_df[likp_df['vbeln'] == order_id]
    delivery_qty = lips_df[lips_df['likp'] == delivery['likp']]['lfimg'].sum()
    
    # Find invoice (VBRK → VBRP)
    invoice = vbrk_df[vbrk_df['vbeln'] == order_id]
    invoice_qty = vbrp_df[vbrp_df['vbrk'] == invoice['vbrk']]['fkimg'].sum()
    
    # Find payment (BSAK)
    payment = bsak_df[bsak_df['belnr'] == invoice['vbrk']]
    cash_amt = payment['dmbtr'].sum() if not payment.empty else 0
    
    # Calculate cycle days
    days_to_delivery = (delivery['wbstk'] - vbap_row['erdat']).days if not delivery.empty else None
    days_to_invoice = (invoice['fkdat'] - vbap_row['erdat']).days if not invoice.empty else None
    days_to_cash = (payment['clearing_date'] - invoice['fkdat']).days if not payment.empty else None
    
    return {
        'order_id': order_id,
        'order_date': vbap_row['erdat'],
        'delivery_qty': delivery_qty,
        'invoice_qty': invoice_qty,
        'cash_received': cash_amt,
        'days_to_cash': days_to_cash,
        'is_fully_paid': (cash_amt >= invoice['netwr'])
    }
```

---

#### Rule 2: GL Reconciliation Linking (Fact Table GL_RECONCILIATION_FACTS)

**Logic:** For each ACDOCA posting, identify the source document (SD, MM, or manual FI entry).

```python
def link_gl_to_source(acdoca_row):
    gl_account = acdoca_row['gkont']
    posting_date = acdoca_row['budat']
    
    if gl_account in ['600001', '600002']:  # Revenue accounts
        # Link to billing document (VBRK)
        source_doc = vbrk_df[
            (vbrk_df['fkdat'] == posting_date) & 
            (vbrk_df['netwr'] == acdoca_row['dmbtr'])
        ]
        source_type = 'SD_BILLING'
        
    elif gl_account == '700001':  # COGS account
        # Link to goods movement (MSEG)
        source_doc = mseg_df[
            (mseg_df['budat'] == posting_date) & 
            (mseg_df['bukrs'] == acdoca_row['bukrs'])
        ]
        source_type = 'MM_GOODS_ISSUE'
        
    elif gl_account == '800001':  # GST Payable
        # Link back to VBRP, calculate GST = NETWR * 18% (or applicable rate)
        source_type = 'SD_GST_CALC'
        
    else:
        source_type = 'FI_MANUAL'
    
    return {
        'source_type': source_type,
        'source_document': source_doc['document_id'] if not source_doc.empty else None,
        'reconciliation_status': 'MATCHED' if not source_doc.empty else 'UNMATCHED'
    }
```

---

#### Rule 3: Inventory Snapshot (Fact Table INVENTORY_FACTS)

**Logic:** Calculate EOD inventory position by material × plant × storage location from MSEG movements.

```python
def calculate_inventory_snapshot(material, plant, storage_loc, snapshot_date):
    # Sum all receipts (MSEG Qtys where movement type = goods receipt)
    receipts = mseg_df[
        (mseg_df['matnr'] == material) &
        (mseg_df['werks'] == plant) &
        (mseg_df['lgort'] == storage_loc) &
        (mseg_df['budat'] <= snapshot_date) &
        (mseg_df['movement_type'].isin(['101']))  # GRN types
    ]['menge'].sum()
    
    # Sum all issues (movement type = goods issue)
    issues = mseg_df[
        (mseg_df['matnr'] == material) &
        (mseg_df['werks'] == plant) &
        (mseg_df['lgort'] == storage_loc) &
        (mseg_df['budat'] <= snapshot_date) &
        (mseg_df['movement_type'].isin(['201', '261']))  # Issue types
    ]['menge'].sum()
    
    closing_balance = receipts - issues
    
    # Days on hand = closing_balance / (avg_daily_sales)
    avg_daily_sales = o2c_df[
        (o2c_df['product'] == material) &
        (o2c_df['delivery_date'] <= snapshot_date) &
        (o2c_df['delivery_date'] > snapshot_date - timedelta(days=90))
    ]['delivery_qty'].sum() / 90
    
    days_on_hand = closing_balance / avg_daily_sales if avg_daily_sales > 0 else 999
    
    return {
        'material': material,
        'plant': plant,
        'storage_location': storage_loc,
        'closing_balance': closing_balance,
        'days_on_hand': days_on_hand,
        'is_obsolete': (days_on_hand > 180) and (avg_daily_sales < 0.1)
    }
```

---

### 3.3 Load Phase

**Target:** SQLite (dev/test) or PostgreSQL (production data warehouse)  
**Method:** Pandas `to_sql()` with `if_exists='append'` (daily incremental loads)

```python
import pandas as pd
from sqlalchemy import create_engine

# Connect to data warehouse
engine = create_engine('sqlite:///novastream_analytics.db')  # or PostgreSQL URI

# Load O2C Facts
o2c_facts_df.to_sql('fct_o2c_transactions', con=engine, if_exists='append', index=False, chunksize=1000)

# Load GL Reconciliation Facts
gl_facts_df.to_sql('fct_gl_reconciliation', con=engine, if_exists='append', index=False, chunksize=1000)

# Load Inventory Facts
inv_facts_df.to_sql('fct_inventory_facts', con=engine, if_exists='append', index=False, chunksize=1000)

# Upsert Dimensions (SCD Type 2 handling for customers, products)
upsert_dim_customer(dim_customer_df, engine)
upsert_dim_product(dim_product_df, engine)
```

---

## 4. Custom Business Logic & Calculations

### 4.1 Days Sales Outstanding (DSO)

**Formula:** Average days from invoice date to cash receipt  
**Calculation:**

```python
def calculate_dso(o2c_facts, period_start, period_end):
    paid_orders = o2c_facts[
        (o2c_facts['is_fully_paid'] == True) &
        (o2c_facts['invoice_date'] >= period_start) &
        (o2c_facts['invoice_date'] <= period_end)
    ]
    
    if len(paid_orders) == 0:
        return None
    
    avg_days_to_cash = paid_orders['days_to_invoice'].mean()
    return avg_days_to_cash
```

**Example Output:**
- Sales Manager views DSO by customer: C1001 = 25 days (Apex Distributors), C1003 = 18 days (ElectroWorld)

---

### 4.2 Gross Margin % by Customer & Product

**Formula:** (Revenue − COGS) / Revenue × 100  
**Calculation:**

```python
def calculate_margin_by_customer_product(o2c_facts, gl_facts, period):
    # Join O2C facts with GL COGS postings
    margin_df = o2c_facts[o2c_facts['period'] == period].groupby(['customer_id', 'product_id']).agg({
        'invoice_amount': 'sum'  # Revenue
    }).reset_index()
    
    # Link to COGS from GL reconciliation facts
    cogs_by_product = gl_facts[
        (gl_facts['gl_account'] == '700001') &
        (gl_facts['period'] == period)
    ].groupby('product_id')['debit_amount'].sum()
    
    margin_df['cogs'] = margin_df['product_id'].map(cogs_by_product)
    margin_df['gross_profit'] = margin_df['invoice_amount'] - margin_df['cogs']
    margin_df['gross_margin_pct'] = (margin_df['gross_profit'] / margin_df['invoice_amount']) * 100
    
    return margin_df
```

**Example Output:**
| Customer | Product | Revenue | COGS | Gross Margin % |
|----------|---------|---------|------|----------------|
| C1001 | NSTV-55 | ₹10,00,000 | ₹5,50,000 | 45% |
| C1003 | NASP-01 | ₹2,50,000 | ₹1,25,000 | 50% |

---

### 4.3 Inventory Turnover Ratio

**Formula:** COGS / Average Inventory  
**Calculation:**

```python
def calculate_inventory_turnover(material, plant, period_month):
    # Get monthly COGS for this material from GL_FACTS filtered by product
    monthly_cogs = gl_facts[
        (gl_facts['gl_account'] == '700001') &
        (gl_facts['product'] == material) &
        (gl_facts['period'] == period_month)
    ]['debit_amount'].sum()
    
    # Get average inventory for the month from INVENTORY_FACTS
    inventory_snapshots = inv_facts[
        (inv_facts['material'] == material) &
        (inv_facts['plant'] == plant) &
        (inv_facts['snapshot_date'] >= period_start) &
        (inv_facts['snapshot_date'] <= period_end)
    ]
    avg_inventory = inventory_snapshots['inventory_value'].mean()
    
    turnover = monthly_cogs / avg_inventory if avg_inventory > 0 else None
    
    return {
        'material': material,
        'monthly_cogs': monthly_cogs,
        'avg_inventory': avg_inventory,
        'turnover_ratio': turnover,
        'days_inventory_outstanding': 365 / turnover if turnover else None
    }
```

---

## 5. Data Quality & Validation Rules

### 5.1 Mandatory Data Integrity Checks

**Rule 1: Sales Order Referential Integrity**

```
EVERY row in O2C_FACTS must satisfy:
- order_id ∈ VBAK.VBELN (valid sales order)
- customer_key ∈ DIM_CUSTOMER.customer_key (valid customer)
- product_key ∈ DIM_PRODUCT.product_key (valid material)
- plant_key ∈ DIM_PLANT.plant_key (valid plant, PL01 or PL02)
- sales_org_key references NV10 (only sales org in scope)
```

**Rule 2: GL Account Validity**

```
EVERY row in GL_RECONCILIATION_FACTS must satisfy:
- gl_account ∈ CHART_OF_ACCOUNTS (one of 17 defined accounts)
- company_code = NV01 (only company code in scope)
- posting_date is in a valid, open period (not closed retroactively)
```

**Rule 3: Inventory Balance Conservation**

```
For EACH material × plant × storage_location on snapshot_date:
  closing_balance = opening_balance + receipts − issues
  
  IF (closing_balance < 0):
    Flag as ERROR (negative stock impossible without correction)
```

**Rule 4: O2C Sequence Logic**

```
For EACH O2C_FACT row:
  order_date ≤ delivery_date ≤ invoice_date ≤ cash_received_date
  
  IF NOT satisfied:
    Flag as ANOMALY and investigate source documents
```

### 5.2 Reconciliation Checks (Daily)

```python
def daily_reconciliation_check():
    """
    Run after ETL loads complete. Validate:
    1. O2C volume: new orders, deliveries, invoices, payments
    2. GL balance consistency: sum of GL debits = sum of credits
    3. Revenue tie-out: sum of VBRK.NETWR = sum of GL 600001/600002
    4. COGS tie-out: sum of MSEG goods issues = GL 700001 postings
    5. Inventory snapshot integrity: no negative balances
    """
    
    # Check 1: O2C volumes
    order_count = o2c_facts.shape[0]
    delivery_count = o2c_facts[o2c_facts['is_fully_delivered']].shape[0]
    invoice_count = o2c_facts[o2c_facts['is_fully_billed']].shape[0]
    paid_count = o2c_facts[o2c_facts['is_fully_paid']].shape[0]
    
    print(f"Orders: {order_count}, Delivered: {delivery_count}, Invoiced: {invoice_count}, Paid: {paid_count}")
    
    # Check 2: GL balance
    gl_total_debit = gl_facts[gl_facts['debit_amount_local'] > 0]['debit_amount_local'].sum()
    gl_total_credit = gl_facts[gl_facts['credit_amount_local'] > 0]['credit_amount_local'].sum()
    
    if abs(gl_total_debit - gl_total_credit) > 0.01:
        print(f"ERROR: GL out of balance! Debits={gl_total_debit}, Credits={gl_total_credit}")
    
    # Check 3: Revenue tie-out
    vbrk_revenue = o2c_facts['invoice_amount'].sum()
    gl_revenue = gl_facts[gl_facts['gl_account'].isin(['600001', '600002'])]['debit_amount_local'].sum()
    
    variance = abs(vbrk_revenue - gl_revenue)
    if variance > 1000:  # Allow for rounding
        print(f"WARNING: Revenue variance ₹{variance} (VBRK={vbrk_revenue}, GL={gl_revenue})")
    
    return {
        'order_count': order_count,
        'gl_balanced': abs(gl_total_debit - gl_total_credit) < 0.01,
        'revenue_tied': variance < 1000
    }
```

---

## 6. Data Warehouse Schema DDL

### Create Fact Tables

```sql
CREATE TABLE fct_o2c_transactions (
    o2c_fact_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_date DATE NOT NULL,
    order_id VARCHAR(20) NOT NULL,
    order_item_id VARCHAR(20) NOT NULL,
    order_amount_local DECIMAL(15,2),
    order_qty DECIMAL(13,3),
    delivery_id VARCHAR(20),
    delivery_date DATE,
    delivery_qty DECIMAL(13,3),
    invoice_id VARCHAR(20),
    invoice_date DATE,
    invoice_amount_local DECIMAL(15,2),
    gst_amount DECIMAL(15,2),
    invoice_qty DECIMAL(13,3),
    cogs_posted_amount DECIMAL(15,2),
    cash_received_date DATE,
    cash_received_amount DECIMAL(15,2),
    is_fully_delivered BOOLEAN,
    is_fully_billed BOOLEAN,
    is_fully_paid BOOLEAN,
    days_to_delivery INT,
    days_to_invoice INT,
    days_to_cash INT,
    o2c_cycle_days INT,
    customer_key INT NOT NULL REFERENCES dim_customer(customer_key),
    product_key INT NOT NULL REFERENCES dim_product(product_key),
    plant_key INT NOT NULL REFERENCES dim_plant(plant_key),
    sales_org_key INT REFERENCES dim_sales_org(sales_org_key),
    dist_channel_key INT REFERENCES dim_dist_channel(dist_channel_key),
    division_key INT REFERENCES dim_division(division_key),
    sales_area_key INT REFERENCES dim_sales_area(sales_area_key),
    company_code_key INT REFERENCES dim_company_code(company_code_key),
    date_key_order INT REFERENCES dim_date(date_key),
    date_key_delivery INT REFERENCES dim_date(date_key),
    date_key_invoice INT REFERENCES dim_date(date_key),
    date_key_cash INT REFERENCES dim_date(date_key),
    etl_load_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    etl_update_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_current BOOLEAN DEFAULT TRUE,
    UNIQUE(order_id, order_item_id)
);

CREATE INDEX idx_o2c_order_date ON fct_o2c_transactions(date_key_order);
CREATE INDEX idx_o2c_customer ON fct_o2c_transactions(customer_key);
CREATE INDEX idx_o2c_product ON fct_o2c_transactions(product_key);
CREATE INDEX idx_o2c_invoice_date ON fct_o2c_transactions(date_key_invoice);
CREATE INDEX idx_o2c_is_paid ON fct_o2c_transactions(is_fully_paid);
```

---

## 7. Testing & Validation

### Test Case 1: O2C End-to-End

**Scenario:** Create a test sales order (VA01), post delivery (VL02N), create invoice (VF01), receive payment (F-28).

**Expected Results:**
- O2C_FACTS row created with all linked documents
- GL postings (debit AR, credit Revenue, debit COGS, credit Inventory, debit Bank, credit AR)
- days_to_cash calculated correctly
- is_fully_paid = TRUE after cash receipt

---

### Test Case 2: GL Reconciliation

**Scenario:** GL account 600001 (Revenue) should match sum of VBRK items for the month.

**Expected:**
```
GL 600001 Balance (from ACDOCA) = ₹50,00,000
Sum of VBRK.NETWR (from O2C_FACTS) = ₹50,00,000
Variance = ₹0 (MATCHED)
```

---

## 8. Glossary & Naming Conventions

| Term | Abbreviation | SAP Example | Analytics Example |
|------|--------------|-------------|-------------------|
| Sales Order Header | VBAK | 0013456789 | order_id in O2C_FACTS |
| Sales Order Item | VBAP | Line 10 | order_item_id in O2C_FACTS |
| Company Code | BUKRS | NV01 | company_code_key |
| Plant | WERKS | PL01 | plant_key |
| Storage Location | LGORT | SL01 | storage_location_code |
| Material | MATNR | NSTV-55 | product_key (references DIM_PRODUCT) |
| Customer | KUNNR | C1001 | customer_key (references DIM_CUSTOMER) |
| GL Account | GKONT | 600001 | gl_account_key (references DIM_GL_ACCOUNT) |

---

**End of Data Schema SRS**
