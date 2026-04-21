# Data Pipeline Architecture
## NovaStream Electronics SAP Analytics ETL Platform

**Project:** NovaStream Electronics Data Analytics Initiative  
**Version:** 1.0  
**Date:** April 21, 2026  
**Audience:** Data Engineering, DevOps, Infrastructure Teams  

---

## 1. Executive Summary

This document outlines the complete data pipeline architecture for NovaStream Electronics' SAP Analytics platform. The pipeline extracts transactional data from the SAP ERP system (FI, MM, SD modules), transforms it according to business rules and dimensional models defined in the Data Schema SRS, and loads it into a cloud-ready data warehouse. The architecture is designed for:

- **Scalability:** From 500–1,000 daily transactions to 100,000+ daily transactions
- **Data Quality:** Automated validation and reconciliation checks
- **Operational Reliability:** Error handling, retry logic, and SLA monitoring
- **Security:** Role-based access control and data encryption
- **Auditability:** Full lineage tracking from SAP source to dashboard

---

## 2. Architecture Overview

### 2.1 High-Level Data Flow

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        SAP ERP SYSTEM (Source Layer)                         │
│  ┌─────────────┬──────────────┬────────────────┬─────────────────────────┐  │
│  │   FI (NV01) │  MM (PL01/02)│  SD (NV10)     │   Master Data           │  │
│  ├─────────────┼──────────────┼────────────────┼─────────────────────────┤  │
│  │ • ACDOCA    │ • MBLK/MSEG  │ • VBAK/VBAP    │ • MARA (Material)       │  │
│  │ • BSAK      │ • MARC       │ • LIKP/LIPS    │ • KNA1 (Customer)       │  │
│  │ • GL Accts  │ • Stock      │ • VBRK/VBRP    │ • Chart of Accounts     │  │
│  │ • Costings  │ •  GRN       │ • Billing      │ • Plant Master          │  │
│  └─────────────┴──────────────┴────────────────┴─────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ RFC / SQL Query
                                    │ (Daily 02:00 AM IST)
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                    ETL ORCHESTRATION LAYER (Airflow / Cron)                  │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ Task 1: Data Extraction (Python script)                               │  │
│  │  - Query VBAK, VBAP, LIKP, VBRK, ACDOCA, MSEG, etc.                │  │
│  │  - Save as CSV/Parquet in staging directory                         │  │
│  │  - Error handling & retry logic                                     │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ Task 2: Data Validation (Quality Checks)                             │  │
│  │  - Schema validation (expected columns & data types)                │  │
│  │  - Null checks on mandatory fields                                  │  │
│  │  - Referential integrity (customer_id, material_id exist)          │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ Task 3: Transformation (Python + Pandas)                            │  │
│  │  - Join VBAK + VBAP + LIKP + VBRK to build O2C_FACTS             │  │
│  │  - Link ACDOCA to source documents for GL reconciliation          │  │
│  │  - Calculate inventory snapshots from MSEG movements              │  │
│  │  - Apply business logic (DSO, margin %, turnover)                │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ Task 4: Dimension Management (SCD Type 2)                           │  │
│  │  - Detect changes in customer/product masters                       │  │
│  │  - Maintain historical records with effective dates                 │  │
│  │  - Generate surrogate keys                                          │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ Task 5: Data Loading (DW Insert)                                     │  │
│  │  - Insert facts into DW (PostgreSQL / SQLite)                       │  │
│  │  - Upsert dimensions                                                 │  │
│  │  - Refresh materialized views (KPI aggregations)                    │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ Task 6: Post-Load Validation & Reconciliation                       │  │
│  │  - GL balance check (debit = credit)                                 │  │
│  │  - Revenue tie-out (VBRK = GL 600001/600002)                        │  │
│  │  - COGS variance reporting                                           │  │
│  │  - Alert on anomalies                                                │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Insert/Upsert
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                       DATA WAREHOUSE LAYER (StarSchema)                      │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Staging Schema (Raw Data — Before Transformation)                   │   │
│  │  ├── stg_vbak (raw sales order headers)                             │   │
│  │  ├── stg_vbak (raw sales order items)                               │   │
│  │  ├── stg_acdoca (raw GL documents)                                  │   │
│  │  └── stg_mseg (raw material documents)                              │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Fact Tables (Transaction-Level Analytics)                          │   │
│  │  ├── fct_o2c_transactions (Order-to-Cash)                           │   │
│  │  ├── fct_gl_reconciliation (GL + Source Matching)                   │   │
│  │  └── fct_inventory_facts (Material Stock Snapshots)                 │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Dimension Tables (Reference & Master Data)                          │   │
│  │  ├── dim_customer (SCD Type 2)                                      │   │
│  │  ├── dim_product (SCD Type 2)                                       │   │
│  │  ├── dim_plant, dim_sales_org, dim_dist_channel, dim_division      │   │
│  │  ├── dim_gl_account, dim_company_code                               │   │
│  │  └── dim_date (Time dimension)                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Aggregated Views (Pre-Calculated KPIs)                              │   │
│  │  ├── vw_o2c_metrics_daily (Revenue, fulfillment, DSO)              │   │
│  │  ├── vw_profitability_by_customer (Margin %, gross profit)         │   │
│  │  ├── vw_inventory_health_daily (Stock levels, DIO, turnover)       │   │
│  │  └── vw_gl_reconciliation_status (Matched GL by account)           │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ SQL Queries
                                    │ (Cached for Performance)
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                    ANALYTICS LAYER (KPI Calculations)                        │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ Business Logic Services (Python Backend)                             │  │
│  │  ├── O2C Pipeline Metrics (days_to_cash, DSO, fulfillment %)       │  │
│  │  ├── Profitability Engine (gross margin %, contribution margin)     │  │
│  │  ├── Inventory Health Calculator (turnover, DIO, safety stock)      │  │
│  │  └── GL Reconciliation Rules (match GL to source documents)         │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ Caching Layer (Redis / Memcached)                                    │  │
│  │  - Cache KPI calculations (refresh every 1 hour)                     │  │
│  │  - Session cache for user dashboards                                 │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ REST API / Streamlit
                                    │ Data Binding
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                  PRESENTATION LAYER (Dashboards & Reports)                   │
│  ┌──────────────────────┬──────────────────────┬──────────────────────────┐  │
│  │  Sales Manager       │  Finance Controller  │  Supply Chain Analyst    │  │
│  │  Dashboard           │  Dashboard           │  Dashboard               │  │
│  ├──────────────────────┼──────────────────────┼──────────────────────────┤  │
│  │ • Revenue KPIs       │ • GL Reconciliation  │ • Inventory Position     │  │
│  │ • O2C Pipeline       │ • Close Automation   │ • Turnover Metrics       │  │
│  │ • Customer Mgmt      │ • Variance Analysis  │ • Supply Chain Health    │  │
│  │ • Fulfillment Rate   │ • AR Aging Review    │ • Procurement Pipeline   │  │
│  └──────────────────────┴──────────────────────┴──────────────────────────┘  │
│                    (Streamlit Web App - Python)                             │
│             Real-Time Data Refresh (every 1–4 hours)                       │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Pipeline Architecture

### 3.1 Extraction Layer

**Purpose:** Reliably extract data from SAP ERP systems without impacting production.

**Components:**

#### 3.1.1 Extraction Methods

| Method | Pros | Cons | Use Case |
|--------|------|------|----------|
| **RFC (Remote Function Call)** | Native SAP; real-time capable; supports FM calls | Requires SAP connectivity; slower for large volumes; licensing | Production extracts; complex joins inside SAP |
| **SQL Direct Query** | Fast; can handle large volumes; easy to optimize | Requires DB access; may lock tables; risk to prod performance | Development/test; batch exports; data warehouse |
| **SAP OData API** | Modern; REST-based; can filter on server; rate-limited | Limited to published entities; requires metadata knowledge | Mobile/real-time; external integrations |
| **File Export (BAPI)** | Decouples SAP from analytics; audit trail; standard | Latency; storage management; requires T-code security | Sensitive data; compliance requirements |

**For NovaStream (Phase 1):** Use **SQL direct query on read replica** (if available) or **RFC batch extraction** during off-peak hours (02:00 AM IST).

#### 3.1.2 Extraction Script (Python)

```python
# File: scripts/01_extract_sap_data.py
import pandas as pd
import pyodbc  # For SQL Server, if available
from sap_rfc_connector import SAPConnection  # Custom RFC wrapper
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SAPDataExtractor:
    def __init__(self, sap_config, output_dir='/data/staging'):
        self.sap = SAPConnection(sap_config)
        self.output_dir = output_dir
        self.extract_date = datetime.now().date()
        
    def extract_vbak_vbap(self):
        """Extract Sales Order Header & Item (VBAK + VBAP)"""
        logger.info("Extracting VBAK/VBAP...")
        
        query = """
        SELECT 
            v.vbeln, v.erdat, v.netwr, v.vkorg, v.vtweg, v.spart,
            p.posnr, p.matnr, p.menge, p.meins, p.werks
        FROM vbak AS v
        INNER JOIN vbap AS p ON v.vbeln = p.vbeln
        WHERE v.bukrs = 'NV01'
          AND v.erdat >= ?
        ORDER BY v.vbeln, p.posnr
        """
        
        # Extract from prior day + today (for reprocessing)
        extract_from = self.extract_date - timedelta(days=1)
        
        try:
            df = pd.read_sql(query, self.sap.connection(), params=[extract_from])
            output_path = f"{self.output_dir}/vbak_vbap_{self.extract_date}.parquet"
            df.to_parquet(output_path, compression='snappy')
            logger.info(f"Extracted {len(df)} VBAK/VBAP rows → {output_path}")
            return df
        except Exception as e:
            logger.error(f"VBAK/VBAP extraction failed: {e}")
            raise
    
    def extract_acdoca(self):
        """Extract GL Documents (ACDOCA)"""
        logger.info("Extracting ACDOCA...")
        
        query = """
        SELECT 
            belnr, buzei, budat, bukrs, gkont, dmbtr, dbcurr,
            xblnr, pswsl
        FROM acdoca
        WHERE bukrs = 'NV01'
          AND budat >= ?
        ORDER BY budat, belnr
        """
        
        extract_from = self.extract_date - timedelta(days=1)
        
        try:
            df = pd.read_sql(query, self.sap.connection(), params=[extract_from])
            output_path = f"{self.output_dir}/acdoca_{self.extract_date}.parquet"
            df.to_parquet(output_path, compression='snappy')
            logger.info(f"Extracted {len(df)} ACDOCA rows → {output_path}")
            return df
        except Exception as e:
            logger.error(f"ACDOCA extraction failed: {e}")
            raise
    
    def extract_mseg_mkpf(self):
        """Extract Material Documents (MSEG + MKPF)"""
        logger.info("Extracting MSEG/MKPF...")
        
        query = """
        SELECT 
            m.mkpf AS mkpf_num, m.posnr, m.matnr, m.menge, m.meins,
            m.werks, m.lgort, m.bwart,
            k.budat, k.bukrs, k.vbeln
        FROM mseg AS m
        INNER JOIN mkpf AS k ON m.mkpf = k.mkpf
        WHERE k.bukrs = 'NV01'
          AND k.budat >= ?
        ORDER BY k.budat, m.mkpf
        """
        
        extract_from = self.extract_date - timedelta(days=1)
        
        try:
            df = pd.read_sql(query, self.sap.connection(), params=[extract_from])
            output_path = f"{self.output_dir}/mseg_mkpf_{self.extract_date}.parquet"
            df.to_parquet(output_path, compression='snappy')
            logger.info(f"Extracted {len(df)} MSEG/MKPF rows → {output_path}")
            return df
        except Exception as e:
            logger.error(f"MSEG/MKPF extraction failed: {e}")
            raise
    
    def extract_master_data(self):
        """Extract Master Data: MARA, KNA1, Chart of Accounts"""
        logger.info("Extracting Master Data...")
        
        # Material Master (MARA)
        mara_query = "SELECT matnr, maktx, mtart, meins FROM mara ORDER BY matnr"
        mara_df = pd.read_sql(mara_query, self.sap.connection())
        mara_df.to_parquet(f"{self.output_dir}/mara_{self.extract_date}.parquet")
        logger.info(f"Extracted {len(mara_df)} MARA records")
        
        # Customer Master (KNA1)
        kna1_query = "SELECT kunnr, name1, land1, city, region FROM kna1 ORDER BY kunnr"
        kna1_df = pd.read_sql(kna1_query, self.sap.connection())
        kna1_df.to_parquet(f"{self.output_dir}/kna1_{self.extract_date}.parquet")
        logger.info(f"Extracted {len(kna1_df)} KNA1 records")
        
        # Chart of Accounts
        coa_query = "SELECT gkont, txt20 FROM t880 WHERE bukrs = 'NV01' ORDER BY gkont"
        coa_df = pd.read_sql(coa_query, self.sap.connection())
        coa_df.to_parquet(f"{self.output_dir}/chart_of_accounts_{self.extract_date}.parquet")
        logger.info(f"Extracted {len(coa_df)} GL Accounts")
    
    def run_full_extract(self):
        """Execute all extractions"""
        logger.info(f"=== SAP Data Extraction Started ({self.extract_date}) ===")
        
        try:
            self.extract_vbak_vbap()
            self.extract_acdoca()
            self.extract_mseg_mkpf()
            self.extract_master_data()
            
            logger.info("=== Extraction Completed Successfully ===")
            return True
        except Exception as e:
            logger.error(f"=== Extraction Failed: {e} ===")
            # Send alert (Slack, email, etc.)
            return False

# Main execution
if __name__ == "__main__":
    sap_config = {
        'ashost': 'sap.novastream.local',
        'sysnr': '00',
        'client': '100',
        'user': 'ANALYTICS_USER',
        'passwd': 'secure_password'  # Use env var in production
    }
    
    extractor = SAPDataExtractor(sap_config)
    success = extractor.run_full_extract()
    exit(0 if success else 1)
```

---

### 3.2 Validation Layer

**Purpose:** Ensure extracted data meets quality standards before transformation.

```python
# File: scripts/02_validate_extracted_data.py
import pandas as pd
from pandera import Column, DataFrameSchema, Check
import logging

logger = logging.getLogger(__name__)

class DataValidator:
    def __init__(self, staging_dir='/data/staging'):
        self.staging_dir = staging_dir
    
    def validate_vbak_schema(self, df):
        """Validate VBAK/VBAP schema"""
        schema = DataFrameSchema({
            'vbeln': Column(str, Check.str_length(10)),
            'erdat': Column('datetime64[ns]', Check.is_in_set(['2026-01-01', '2026-12-31'])),
            'netwr': Column(float, Check.greater_than_or_equal_to(0)),
            'matnr': Column(str),
            'menge': Column(float, Check.greater_than(0)),
            'werks': Column(str, Check.isin(['PL01', 'PL02']))
        })
        
        try:
            schema.validate(df)
            logger.info(f"✓ VBAK/VBAP validation passed ({len(df)} rows)")
            return True
        except Exception as e:
            logger.error(f"✗ VBAK/VBAP validation failed: {e}")
            return False
    
    def validate_referential_integrity(self, vbak_df, kna1_df, mara_df):
        """Check that all FK references exist"""
        # Customer FK
        invalid_customers = vbak_df[~vbak_df['kunnr'].isin(kna1_df['kunnr'])]
        if len(invalid_customers) > 0:
            logger.warning(f"⚠ {len(invalid_customers)} invalid customer IDs found")
        
        # Material FK
        invalid_materials = vbak_df[~vbak_df['matnr'].isin(mara_df['matnr'])]
        if len(invalid_materials) > 0:
            logger.warning(f"⚠ {len(invalid_materials)} invalid material IDs found")
        
        # Plant FK
        valid_plants = ['PL01', 'PL02']
        invalid_plants = vbak_df[~vbak_df['werks'].isin(valid_plants)]
        if len(invalid_plants) > 0:
            logger.warning(f"⚠ {len(invalid_plants)} invalid plant codes found")
        
        return len(invalid_customers) == 0 and len(invalid_materials) == 0
    
    def validate_no_negatives(self, df, numeric_cols):
        """Check for impossible negative amounts/quantities"""
        for col in numeric_cols:
            negatives = df[df[col] < 0]
            if len(negatives) > 0:
                logger.error(f"✗ {col} has {len(negatives)} negative values (should be >= 0)")
                return False
        return True
    
    def run_all_validations(self):
        """Execute all quality checks"""
        logger.info("=== Data Validation Started ===")
        
        # Load staged data
        vbak_df = pd.read_parquet(f"{self.staging_dir}/vbak_vbap_*.parquet")
        acdoca_df = pd.read_parquet(f"{self.staging_dir}/acdoca_*.parquet")
        mseg_df = pd.read_parquet(f"{self.staging_dir}/mseg_mkpf_*.parquet")
        kna1_df = pd.read_parquet(f"{self.staging_dir}/kna1_*.parquet")
        mara_df = pd.read_parquet(f"{self.staging_dir}/mara_*.parquet")
        
        # Run validations
        all_pass = True
        all_pass &= self.validate_vbak_schema(vbak_df)
        all_pass &= self.validate_referential_integrity(vbak_df, kna1_df, mara_df)
        all_pass &= self.validate_no_negatives(vbak_df, ['menge', 'netwr'])
        all_pass &= self.validate_no_negatives(acdoca_df, ['dmbtr'])
        
        logger.info(f"=== Validation {'Passed' if all_pass else 'Failed'} ===")
        return all_pass
```

---

### 3.3 Transformation Layer

**Purpose:** Apply business logic, dimensional mapping, and aggregations.

```python
# File: scripts/03_transform_to_facts.py
import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class O2CTransformer:
    def __init__(self, dwh_connection):
        self.dwh = dwh_connection
    
    def build_o2c_facts(self, vbak_df, vbap_df, likp_df, vbrk_df, bsak_df):
        """
        Build O2C_FACTS by linking sales order items through 
        delivery → invoice → cash receipt
        """
        logger.info("Building O2C Facts...")
        
        # Start with order items (VBAP)
        o2c = vbap_df.copy()
        
        # Add order header data (VBAK)
        o2c = o2c.merge(vbak_df[['vbeln', 'erdat', 'netwr']], 
                        on='vbeln', suffixes=('_item', '_header'))
        
        # Left join delivery (LIKP)
        o2c = o2c.merge(likp_df[['vbeln', 'likp', 'wbstk']], 
                        on='vbeln', how='left')
        
        # Left join invoice (VBRK)
        o2c = o2c.merge(vbrk_df[['vbeln', 'vbrk', 'fkdat', 'netwr']], 
                        on='vbeln', how='left', suffixes=('_delivery', '_invoice'))
        
        # Left join payment (BSAK) — need invoice reference
        o2c = o2c.merge(bsak_df[['belnr', 'clearing_date', 'dmbtr']], 
                        left_on='vbrk', right_on='belnr', how='left')
        
        # Calculate cycle days
        o2c['days_to_delivery'] = (o2c['wbstk'] - o2c['erdat']).dt.days
        o2c['days_to_invoice'] = (o2c['fkdat'] - o2c['erdat']).dt.days
        o2c['days_to_cash'] = (o2c['clearing_date'] - o2c['fkdat']).dt.days
        o2c['o2c_cycle_days'] = (o2c['clearing_date'] - o2c['erdat']).dt.days
        
        # Flags
        o2c['is_fully_delivered'] = o2c['likp'].notna()
        o2c['is_fully_billed'] = o2c['vbrk'].notna()
        o2c['is_fully_paid'] = (o2c['dmbtr'] >= o2c['netwr_invoice']).fillna(False)
        
        logger.info(f"Built {len(o2c)} O2C fact rows")
        return o2c
    
    def add_dimensional_keys(self, o2c_df, dim_customer, dim_product, dim_plant):
        """Add surrogate keys for dimensions"""
        logger.info("Adding dimensional keys...")
        
        o2c_df = o2c_df.merge(
            dim_customer[['customer_id', 'customer_key']], 
            left_on='kunnr', right_on='customer_id', how='left'
        )
        
        o2c_df = o2c_df.merge(
            dim_product[['material_code', 'product_key']], 
            left_on='matnr', right_on='material_code', how='left'
        )
        
        o2c_df = o2c_df.merge(
            dim_plant[['plant_id', 'plant_key']], 
            left_on='werks', right_on='plant_id', how='left'
        )
        
        # Add date keys
        o2c_df['date_key_order'] = o2c_df['erdat'].dt.strftime('%Y%m%d').astype(int)
        o2c_df['date_key_delivery'] = o2c_df['wbstk'].dt.strftime('%Y%m%d').astype(int)
        o2c_df['date_key_invoice'] = o2c_df['fkdat'].dt.strftime('%Y%m%d').astype(int)
        o2c_df['date_key_cash'] = o2c_df['clearing_date'].dt.strftime('%Y%m%d').astype(int)
        
        logger.info(f"Added dimensional keys to {len(o2c_df)} rows")
        return o2c_df

class GLReconciliationTransformer:
    def __init__(self):
        pass
    
    def link_gl_to_sources(self, acdoca_df, vbrk_df, mseg_df):
        """
        Link each GL posting to its source document (SD invoice, MM goods issue, etc.)
        """
        logger.info("Building GL Reconciliation Facts...")
        
        recon = acdoca_df.copy()
        recon['source_type'] = 'UNMATCHED'
        recon['source_doc'] = None
        
        # Revenue postings (GL 600001, 600002)
        revenue_rows = recon[recon['gkont'].isin(['600001', '600002'])].index
        matched = recon.loc[revenue_rows].merge(
            vbrk_df[['fkdat', 'netwr', 'vbrk']], 
            left_on=['budat', 'dmbtr'], 
            right_on=['fkdat', 'netwr'], 
            how='left'
        )
        recon.loc[revenue_rows, 'source_type'] = 'SD_BILLING'
        recon.loc[revenue_rows, 'source_doc'] = matched['vbrk']
        
        # COGS postings (GL 700001)
        cogs_rows = recon[recon['gkont'] == '700001'].index
        matched = recon.loc[cogs_rows].merge(
            mseg_df[['budat', 'mkpf']], 
            left_on=['budat'], 
            right_on=['budat'], 
            how='left'
        )
        recon.loc[cogs_rows, 'source_type'] = 'MM_GOODS_ISSUE'
        recon.loc[cogs_rows, 'source_doc'] = matched['mkpf']
        
        recon['reconciliation_status'] = recon['source_doc'].apply(
            lambda x: 'MATCHED' if pd.notna(x) else 'UNMATCHED'
        )
        
        logger.info(f"Linked {(recon['reconciliation_status'] == 'MATCHED').sum()} of {len(recon)} GL rows to sources")
        return recon
```

---

### 3.4 Load Layer

**Purpose:** Efficiently insert facts and dimensions into the data warehouse.

```python
# File: scripts/04_load_to_dwh.py
from sqlalchemy import create_engine, text
import pandas as pd
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DWHLoader:
    def __init__(self, dwh_uri='postgresql://user:pass@localhost/novastream_dw'):
        self.engine = create_engine(dwh_uri)
    
    def load_fact_table(self, fact_df, table_name, batch_size=1000):
        """Insert fact rows into DW (append-only)"""
        logger.info(f"Loading {len(fact_df)} rows into {table_name}...")
        
        try:
            fact_df.to_sql(
                table_name, 
                con=self.engine, 
                if_exists='append', 
                index=False, 
                method='multi',
                chunksize=batch_size
            )
            logger.info(f"✓ Successfully loaded {len(fact_df)} rows into {table_name}")
        except Exception as e:
            logger.error(f"✗ Failed to load {table_name}: {e}")
            raise
    
    def upsert_dimension(self, dim_df, table_name, key_column):
        """Upsert dimension (SCD Type 2 handling)"""
        logger.info(f"Upserting {len(dim_df)} rows into {table_name}...")
        
        # Check for changes
        existing = pd.read_sql(
            f"SELECT * FROM {table_name} WHERE is_current = TRUE", 
            self.engine
        )
        
        # New rows
        new_rows = dim_df[~dim_df[key_column].isin(existing[key_column])]
        new_rows['is_current'] = True
        new_rows['etl_load_date'] = datetime.now()
        
        # Changed rows
        changed = dim_df.merge(
            existing, on=key_column, how='inner', 
            suffixes=('_new', '_old')
        )
        changed = changed[changed[[c for c in changed.columns if c.endswith('_new')]].ne(
            changed[[c for c in changed.columns if c.endswith('_old')]].values
        ).any(axis=1)]
        
        if len(changed) > 0:
            # Mark old records as historical
            old_ids = changed[key_column].values
            with self.engine.connect() as conn:
                conn.execute(
                    text(f"UPDATE {table_name} SET is_current = FALSE WHERE {key_column} IN :ids"),
                    {'ids': tuple(old_ids)}
                )
                conn.commit()
            
            # Insert new versions
            changed_new = changed[[c for c in changed.columns if not c.endswith('_old')]].copy()
            changed_new.columns = changed_new.columns.str.replace('_new', '')
            changed_new['is_current'] = True
            changed_new['etl_load_date'] = datetime.now()
            new_rows = pd.concat([new_rows, changed_new])
        
        # Load all new/updated
        if len(new_rows) > 0:
            new_rows.to_sql(table_name, con=self.engine, if_exists='append', index=False)
            logger.info(f"✓ Upserted {len(new_rows)} rows into {table_name}")
    
    def refresh_materialized_views(self):
        """Refresh pre-calculated KPI views"""
        logger.info("Refreshing materialized views...")
        
        views_to_refresh = [
            'vw_o2c_metrics_daily',
            'vw_profitability_by_customer',
            'vw_inventory_health_daily',
            'vw_gl_reconciliation_status'
        ]
        
        with self.engine.connect() as conn:
            for view_name in views_to_refresh:
                try:
                    conn.execute(text(f"REFRESH MATERIALIZED VIEW {view_name}"))
                    logger.info(f"✓ Refreshed {view_name}")
                except Exception as e:
                    logger.warning(f"⚠ Failed to refresh {view_name}: {e}")
            conn.commit()

# Main execution
def load_all_to_dwh(staging_dir, dwh_uri):
    loader = DWHLoader(dwh_uri)
    
    # Load facts
    o2c_df = pd.read_parquet(f"{staging_dir}/o2c_facts.parquet")
    loader.load_fact_table(o2c_df, 'fct_o2c_transactions')
    
    gl_df = pd.read_parquet(f"{staging_dir}/gl_recon_facts.parquet")
    loader.load_fact_table(gl_df, 'fct_gl_reconciliation')
    
    inv_df = pd.read_parquet(f"{staging_dir}/inventory_facts.parquet")
    loader.load_fact_table(inv_df, 'fct_inventory_facts')
    
    # Upsert dimensions
    customer_df = pd.read_parquet(f"{staging_dir}/dim_customer.parquet")
    loader.upsert_dimension(customer_df, 'dim_customer', 'customer_id')
    
    # Refresh views
    loader.refresh_materialized_views()
    
    logger.info("=== DWH Load Complete ===")
```

---

## 4. Orchestration & Scheduling

### 4.1 Apache Airflow DAG

**Purpose:** Schedule and monitor daily ETL pipeline execution.

```python
# File: dags/novastream_analytics_daily.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import logging

default_args = {
    'owner': 'analytics-team',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': days_ago(1),
    'email_on_failure': ['analytics-alert@novastream.local'],
}

dag = DAG(
    'novastream_analytics_daily',
    default_args=default_args,
    description='Daily SAP Analytics ETL Pipeline',
    schedule_interval='0 2 * * *',  # 02:00 AM IST daily
    catchup=False,
)

# Import transformation functions
from scripts.extract import SAPDataExtractor
from scripts.validate import DataValidator
from scripts.transform import O2CTransformer, GLReconciliationTransformer
from scripts.load import DWHLoader

# Task 1: Extract from SAP
def extract_task():
    extractor = SAPDataExtractor(sap_config={'ashost': 'sap.prod', ...})
    return extractor.run_full_extract()

extract = PythonOperator(
    task_id='extract_sap_data',
    python_callable=extract_task,
    dag=dag,
)

# Task 2: Validate
def validate_task():
    validator = DataValidator()
    return validator.run_all_validations()

validate = PythonOperator(
    task_id='validate_data',
    python_callable=validate_task,
    dag=dag,
)

# Task 3: Transform (O2C)
def transform_o2c_task():
    # Load staged data
    transformer = O2CTransformer(None)
    # ... build O2C facts
    pass

transform_o2c = PythonOperator(
    task_id='transform_o2c_facts',
    python_callable=transform_o2c_task,
    dag=dag,
)

# Task 4: Transform (GL Reconciliation)
def transform_gl_task():
    transformer = GLReconciliationTransformer()
    # ... link GL to sources
    pass

transform_gl = PythonOperator(
    task_id='transform_gl_facts',
    python_callable=transform_gl_task,
    dag=dag,
)

# Task 5: Load to DWH
def load_task():
    loader = DWHLoader(dwh_uri='postgresql://...')
    # ... load facts and dimensions
    pass

load = PythonOperator(
    task_id='load_to_dwh',
    python_callable=load_task,
    dag=dag,
)

# Task 6: Reconciliation Check
def reconcile_task():
    from scripts.validate import daily_reconciliation_check
    return daily_reconciliation_check()

reconcile = PythonOperator(
    task_id='post_load_reconciliation',
    python_callable=reconcile_task,
    dag=dag,
)

# Task 7: Alert on Failures
alert = BashOperator(
    task_id='send_alert',
    bash_command='curl -X POST {{ var.value.slack_webhook }} -d "Analytics ETL failed"',
    trigger_rule='one_failed',
    dag=dag,
)

# DAG Dependencies
extract >> validate >> [transform_o2c, transform_gl] >> load >> reconcile >> alert
```

---

### 4.2 Alternative: Cron-based Scheduling (Lightweight)

For MVP without Airflow:

```bash
# File: /etc/cron.d/novastream_analytics
# Run daily at 02:00 AM IST (8:30 PM UTC previous day)

0 2 * * * analytics_user /opt/novastream_analytics/scripts/run_daily_etl.sh >> /var/log/novastream_etl.log 2>&1
```

```bash
# File: scripts/run_daily_etl.sh
#!/bin/bash
set -e

LOG_FILE="/var/log/novastream_etl_$(date +%Y%m%d_%H%M%S).log"

echo "Starting ETL at $(date)" >> $LOG_FILE

# Step 1: Extract
python /opt/scripts/01_extract_sap_data.py >> $LOG_FILE 2>&1
if [ $? -ne 0 ]; then
    echo "Extract failed" >> $LOG_FILE
    exit 1
fi

# Step 2: Validate
python /opt/scripts/02_validate_extracted_data.py >> $LOG_FILE 2>&1

# Step 3–5: Transform & Load
python /opt/scripts/03_transform_to_facts.py >> $LOG_FILE 2>&1
python /opt/scripts/04_load_to_dwh.py >> $LOG_FILE 2>&1

# Step 6: Reconciliation
python /opt/scripts/05_post_load_reconciliation.py >> $LOG_FILE 2>&1

echo "ETL completed at $(date)" >> $LOG_FILE
```

---

## 5. Monitoring & Alerting

### 5.1 SLA Monitoring

```python
# File: monitoring/sla_check.py
import pandas as pd
from datetime import datetime, timedelta
import requests

class SLAMonitor:
    def __init__(self, dwh_connection):
        self.dwh = dwh_connection
    
    def check_daily_sla(self):
        """
        Monitor ETL SLAs:
        1. Extract completes by 02:15 AM
        2. Load completes by 02:45 AM
        3. Daily row counts match expected ranges
        4. No unmatched GL items >1%
        """
        
        # Check ETL completion time
        latest_load = pd.read_sql(
            "SELECT MAX(etl_load_date) as latest FROM fct_o2c_transactions",
            self.dwh
        )['latest'][0]
        
        load_time = latest_load.hour * 60 + latest_load.minute
        sla_time = 2 * 60 + 45  # 02:45 AM
        
        if load_time > sla_time:
            self.alert_slack(f"⚠ ETL load completed at {load_time}, exceeds SLA of {sla_time}")
        
        # Check daily volume
        today_rows = pd.read_sql(
            f"""
            SELECT COUNT(*) as cnt FROM fct_o2c_transactions 
            WHERE date_key_order = {datetime.now().strftime('%Y%m%d')}
            """,
            self.dwh
        )['cnt'][0]
        
        if today_rows < 50:  # Minimum expected daily orders
            self.alert_slack(f"⚠ Low daily order volume: {today_rows} (expected >50)")
        
        # Check GL reconciliation
        unmatched_pct = pd.read_sql(
            """
            SELECT COUNT(*) * 100.0 / (SELECT COUNT(*) FROM fct_gl_reconciliation) 
            as unmatched_pct
            FROM fct_gl_reconciliation 
            WHERE reconciliation_status = 'UNMATCHED'
            """,
            self.dwh
        )['unmatched_pct'][0]
        
        if unmatched_pct > 1:
            self.alert_slack(f"⚠ GL reconciliation: {unmatched_pct:.1f}% unmatched (SLA: <1%)")
    
    def alert_slack(self, message):
        """Send alert to Slack"""
        slack_webhook = "https://hooks.slack.com/services/..."
        requests.post(slack_webhook, json={'text': message})
```

---

## 6. Data Quality & Testing

### 6.1 Unit Tests for Transformations

```python
# File: tests/test_transformations.py
import pytest
import pandas as pd

def test_o2c_cycle_days():
    """Test that days_to_cash is calculated correctly"""
    test_data = {
        'erdat': pd.to_datetime(['2026-04-15']),
        'fkdat': pd.to_datetime(['2026-04-17']),
        'clearing_date': pd.to_datetime(['2026-05-05'])
    }
    df = pd.DataFrame(test_data)
    
    df['days_to_invoice'] = (df['fkdat'] - df['erdat']).dt.days
    df['days_to_cash'] = (df['clearing_date'] - df['fkdat']).dt.days
    
    assert df['days_to_invoice'][0] == 2, "Days to invoice should be 2"
    assert df['days_to_cash'][0] == 18, "Days to cash should be 18"

def test_margin_calculation():
    """Test gross margin calculation"""
    test_data = {
        'invoice_amount': [100000],
        'cogs': [55000]
    }
    df = pd.DataFrame(test_data)
    
    df['gross_margin_pct'] = ((df['invoice_amount'] - df['cogs']) / df['invoice_amount']) * 100
    
    assert df['gross_margin_pct'][0] == 45.0, "Margin should be 45%"

def test_inventory_turnover():
    """Test inventory turnover ratio"""
    monthly_cogs = 550000
    avg_inventory = 110000
    
    turnover = monthly_cogs / avg_inventory
    dio = 365 / turnover
    
    assert turnover == 5.0, "Turnover should be 5x"
    assert dio == 73, "DIO should be 73 days"
```

---

## 7. Architecture Diagram (Mermaid)

```mermaid
graph LR
    A["SAP ERP\n(FI/MM/SD)"] -->|RFC/SQL| B["Extract Layer\n(Python)"]
    B -->|Parquet| C["Staging\n(Raw Data)"]
    C --> D["Validate\n(Schema/Refs)"]
    D --> E["Transform\n(Join/Agg)"]
    E --> F["Load\n(DW Insert)"]
    F --> G["Data Warehouse\n(Postgres)"]
    G -->|SQL Queries| H["Analytics Layer\n(KPI Calc)"]
    H -->|REST/Streamlit| I["Dashboards\n(3 Personas)"]
    
    J["Airflow\n(Orchestration)"] -->|Schedule| B
    K["Monitoring\n(SLA)"] -->|Check| F
    
    style A fill:#ff9999
    style B fill:#ffcc99
    style G fill:#99ccff
    style I fill:#99ff99
    style J fill:#ffff99
```

---

## 8. Deployment Checklist

- [ ] Deploy data warehouse schema (DDL scripts)
- [ ] Configure SAP RFC / SQL connectivity
- [ ] Set up extraction scripts with error handling
- [ ] Deploy transformation & load scripts
- [ ] Configure Airflow DAG and schedule
- [ ] Set up monitoring & alerting (SLA checks)
- [ ] Run full test cycle (extract → load → validate)
- [ ] Activate Streamlit dashboard
- [ ] Train users on dashboards
- [ ] Go-live production ETL

---

**End of Data Pipeline Architecture Document**
