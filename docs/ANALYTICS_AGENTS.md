# ANALYTICS_AGENTS.md
## Data Engineering Rules & AI Coding Agent Guidelines for NovaStream SAP Analytics

**Project:** NovaStream Electronics Data Analytics Platform  
**Version:** 1.0  
**Date:** April 21, 2026  
**Audience:** AI Coding Agents, Python Developers, DevOps Engineers  

---

## 1. Purpose

This document defines strict rules, naming conventions, and best practices for AI coding agents (Claude, GitHub Copilot, etc.) generating Python code for the SAP analytics platform. The rules ensure:

1. **SAP Semantic Accuracy:** Code respects SAP table structures, data types, and business logic
2. **Consistency:** All generated code follows uniform naming, structure, and patterns
3. **Data Integrity:** Mandatory validation and reconciliation rules prevent data quality issues
4. **Auditability:** Code includes logging, error handling, and transaction tracking
5. **Maintainability:** Code is modular, documented, and testable

---

## 2. Naming Conventions (Mandatory)

### 2.1 SAP Domain Variables

**Rule:** Use SAP-standard abbreviations for all variables referencing SAP entities. This ensures code readers with SAP knowledge immediately understand the context.

#### 2.1.1 Company Code & Organizational Units

| SAP Term | Standard Variable | Example | Notes |
|----------|-------------------|---------|-------|
| Company Code | `bukrs` | `bukrs = 'NV01'` | Always 4 characters, left-padded |
| Plant | `werks` | `werks = 'PL01'` | Always 4 characters |
| Storage Location | `lgort` | `lgort = 'SL01'` | 4 characters; valid set: {SL01, SL02, SL03, SL04, SL05} |
| Sales Organization | `vkorg` | `vkorg = 'NV10'` | Always 4 characters |
| Distribution Channel | `vtweg` | `vtweg = '10'` | 2 characters; valid set: {10, 20} |
| Division | `spart` | `spart = 'EL'` | 2 characters; valid set: {EL, AC} |
| Purchasing Organization | `ekorg` | `ekorg = 'NVP1'` | Always 4 characters |

**Example (Correct):**
```python
def extract_sales_by_org(bukrs='NV01', vkorg='NV10', vtweg='10', spart='EL'):
    """
    Extract sales data for a specific Sales Area (vkorg + vtweg + spart).
    Args:
        bukrs: Company Code (NV01)
        vkorg: Sales Organization (NV10)
        vtweg: Distribution Channel (10 or 20)
        spart: Division (EL or AC)
    """
    query = f"""
    SELECT vbeln, erdat, netwr 
    FROM vbak 
    WHERE bukrs = '{bukrs}' 
      AND vkorg = '{vkorg}' 
      AND vtweg = '{vtweg}' 
      AND spart = '{spart}'
    """
```

---

#### 2.1.2 SAP Master Data & Transactional Entities

| Entity | Variable | Example | Notes |
|--------|----------|---------|-------|
| Material Number | `matnr` | `matnr = 'NSTV-55'` | 18 characters max, alphanumeric |
| Material Type | `mtart` | `mtart = 'FERT'` | Valid: FERT (finished), ROH (raw), HAWA (trading) |
| Customer Number | `kunnr` | `kunnr = 'C1001'` | Format: C####, max 10 characters |
| Customer Name | `kname` or `name1` | `kname = 'Apex Distributors'` | 80 characters max |
| Vendor/Supplier | `lifnr` | `lifnr = 'SUP001'` | Similar to customer number format |
| Sales Order Number | `vbeln` | `vbeln = '0013456789'` | 10 characters, zero-padded |
| Sales Order Item | `posnr` | `posnr = '10'` | 2 characters, zero-padded (10, 20, 30, ...) |
| Delivery Number | `likp` | `likp = '0008765432'` | 10 characters (same format as VBELN) |
| Delivery Item | `lips_posnr` | `lips_posnr = '10'` | 6 characters in real SAP; simplify to '10', '20', etc. |
| Invoice/Billing Number | `vbrk` | `vbrk = '0000234561'` | 10 characters, zero-padded |
| GL Account Number | `gkont` | `gkont = '600001'` | 6 characters for NovaStream (600001, 700001, etc.) |
| GL Document Number | `belnr` | `belnr = '0000345678'` | 10 characters, zero-padded |
| GL Item Number | `buzei` | `buzei = '01'` | 3 characters, zero-padded |

**Example (Correct):**
```python
def match_sales_order_to_invoice(vbeln='0013456789', matnr='NSTV-55', kunnr='C1001'):
    """Link a sales order to its corresponding invoice."""
    sales_order = fetch_vbak(vbeln, bukrs='NV01')
    invoice = fetch_vbrk(vbeln, bukrs='NV01')
    
    return {
        'vbeln': vbeln,
        'matnr': matnr,
        'kunnr': kunnr,
        'order_date': sales_order['erdat'],
        'invoice_date': invoice['fkdat'] if invoice else None
    }
```

---

#### 2.1.3 Dates & Time Periods

| Term | Variable | Format | Example | Notes |
|------|----------|--------|---------|-------|
| Posting Date | `budat` | YYYY-MM-DD | 2026-04-15 | GL posting date; always ≤ document date |
| Document Date | `erdat` (orders), `fkdat` (invoices) | YYYY-MM-DD | 2026-04-15 | Business document creation date |
| Fiscal Period | `monat` | Integer 1-12 | 1 (April in Indian FY) | April=1, May=2, ..., March=12 for April-March FY |
| Fiscal Year | `gjahr` | YYYY | 2026 | April 2026 – March 2027 = FY 2026 |
| Company Code Key | `bukrs_key` or `company_code_key` | INT | 1 | Surrogate key for dimension table |

**Example (Correct):**
```python
def extract_by_fiscal_period(bukrs='NV01', gjahr=2026, monat=1):
    """Extract April transactions (monat=1) from FY 2026."""
    query = f"""
    SELECT belnr, buzei, budat, gkont, dmbtr
    FROM acdoca
    WHERE bukrs = '{bukrs}'
      AND gjahr = {gjahr}
      AND monat = {monat}
    ORDER BY budat, belnr
    """
```

---

#### 2.1.4 Amounts & Quantities

| Term | Variable | Data Type | Example | Notes |
|------|----------|-----------|---------|-------|
| Amount (Local Currency) | `dmbtr`, `netwr`, `menge_value` | DECIMAL(15,2) for ₹, DECIMAL(13,3) for Qty | 1062000.00 | INR amounts with 2 decimals; quantities 3 decimals |
| Currency Code | `waers` | CHAR(3) | INR | Always INR for NovaStream (except inter-company: USD) |
| Quantity | `menge` | DECIMAL(13,3) | 20.000 | Always 3 decimal places (piece, kg, liter) |
| Unit of Measure | `meins` | CHAR(3) | EA, KG, LT | Standard SAP UOM codes |

**Example (Correct):**
```python
def calculate_order_value(menge=20.000, unit_price=45000.00, waers='INR'):
    """Calculate total order value in local currency."""
    if waers != 'INR':
        raise ValueError(f"Currency {waers} not supported; expected INR")
    
    order_value = menge * unit_price
    return round(order_value, 2)  # Always round to 2 decimals for currency
```

---

### 2.2 Dimension & Fact Table Naming

**Rule:** Distinguish between dimension and fact tables using prefixes; use lowercase with underscores.

#### 2.2.1 Fact Table Naming

**Pattern:** `fct_{domain}_{subject}`

| Fact Table | Database Name | Purpose | Granularity |
|------------|---------------|---------|------------|
| Order-to-Cash | `fct_o2c_transactions` | O2C pipeline tracking | 1 row per sales order item |
| GL Reconciliation | `fct_gl_reconciliation` | GL posting lineage | 1 row per GL document line |
| Inventory | `fct_inventory_facts` | Daily stock snapshots | 1 row per material-plant-location per day |
| Material Movements | `fct_material_movements` | Inbound/outbound goods | 1 row per MSEG line item |
| Revenue Recognition | `fct_revenue_facts` | Revenue by dimension | 1 row per invoice item |

**Example (Correct):**
```python
# Insert into fact table
fact_data = pd.DataFrame({
    'o2c_fact_id': [1001, 1002],
    'order_id': ['0013456789', '0013456790'],
    'customer_key': [102, 103],
    'product_key': [305, 306],
    'days_to_cash': [18, 25]
})

fact_data.to_sql('fct_o2c_transactions', con=engine, if_exists='append', index=False)
```

---

#### 2.2.2 Dimension Table Naming

**Pattern:** `dim_{entity}`

| Dimension Table | Database Name | Key Field | SCD Type |
|-----------------|---------------|-----------|----------|
| Customer | `dim_customer` | customer_key | Type 2 (track history) |
| Product/Material | `dim_product` | product_key | Type 2 (track cost changes) |
| Plant | `dim_plant` | plant_key | Type 1 (overwrite) |
| Sales Org | `dim_sales_org` | sales_org_key | Type 1 |
| Distribution Channel | `dim_dist_channel` | dist_channel_key | Type 1 |
| Division | `dim_division` | division_key | Type 1 |
| GL Account | `dim_gl_account` | gl_account_key | Type 1 |
| Company Code | `dim_company_code` | company_code_key | Type 1 |
| Date | `dim_date` | date_key | N/A (static) |

**Example (Correct):**
```python
# Create dimension record with SCD Type 2
customer_record = {
    'customer_id': 'C1001',
    'customer_name': 'Apex Distributors',
    'city': 'Delhi',
    'effective_from_date': '2026-01-01',
    'effective_to_date': None,
    'is_current': True
}

# Insert into dimension
pd.DataFrame([customer_record]).to_sql('dim_customer', con=engine, if_exists='append', index=False)
```

---

### 2.3 Function & Module Naming

**Rule:** Use clear, action-oriented names that describe extraction, transformation, or business logic.

#### 2.3.1 Extraction Functions

**Pattern:** `extract_{sap_table}` or `extract_{business_entity}`

```python
def extract_vbak_vbap(bukrs='NV01', extract_date=None):
    """Extract sales orders and items from VBAK/VBAP."""
    pass

def extract_acdoca(bukrs='NV01', extract_date=None):
    """Extract GL documents from ACDOCA."""
    pass

def extract_material_master(werks=None):
    """Extract material master (MARA) across plants."""
    pass

def extract_customer_master(bukrs='NV01'):
    """Extract customer master (KNA1) for company code."""
    pass
```

---

#### 2.3.2 Transformation Functions

**Pattern:** `transform_{fact_table}` or `calculate_{business_metric}`

```python
def transform_to_o2c_facts(vbak_df, vbap_df, likp_df, vbrk_df, bsak_df):
    """
    Transform raw sales/delivery/invoice/payment data into O2C fact table.
    Returns: DataFrame with O2C metrics (days_to_cash, DSO, fulfillment %, etc.)
    """
    pass

def calculate_days_sales_outstanding(o2c_facts_df, period_start, period_end):
    """
    Calculate DSO (Days Sales Outstanding) for a period.
    DSO = Avg days from invoice to payment.
    """
    pass

def calculate_gross_margin_by_customer(o2c_facts_df, cogs_by_product_df):
    """
    Calculate gross margin % by customer.
    Margin % = (Revenue - COGS) / Revenue * 100
    """
    pass

def link_gl_to_source_documents(acdoca_df, vbrk_df, mseg_df):
    """
    Link each GL posting to its source document (SD invoice, MM goods issue).
    Creates GL reconciliation lineage.
    """
    pass
```

---

#### 2.3.3 Validation & Reconciliation Functions

**Pattern:** `validate_{entity}` or `reconcile_{process}`

```python
def validate_referential_integrity(o2c_df, customer_dim, product_dim, plant_dim):
    """
    Check that all O2C rows reference valid customers, products, and plants.
    Returns: (is_valid: bool, error_rows: DataFrame)
    """
    pass

def validate_no_negative_amounts(df, numeric_columns):
    """
    Flag rows with negative amounts/quantities (which are invalid).
    Returns: (is_valid: bool, invalid_rows: DataFrame)
    """
    pass

def reconcile_revenue_to_gl(vbrk_revenue_total, gl_600001_balance, tolerance_inr=1000):
    """
    Three-way reconciliation: VBRK revenue ↔ GL 600001 balance.
    Flag variance if |difference| > tolerance.
    """
    pass

def reconcile_cogs_to_inventory(gl_700001_cogs, gl_200001_inventory_delta):
    """
    Match COGS posting (GL 700001) to inventory reduction (GL 200001).
    """
    pass

def reconcile_gl_by_account(acdoca_df, gl_account):
    """
    For a specific GL account, sum all debits/credits and flag if unbalanced.
    Returns: {account: '600001', total_debit: X, total_credit: Y, balanced: bool}
    """
    pass
```

---

### 2.4 Variable Naming for Data Frames & Series

**Rule:** Clearly indicate whether a variable holds a DataFrame, Series, dict, or scalar.

#### 2.4.1 DataFrame Variables

**Pattern:** Suffix with `_df` to indicate pandas DataFrame

```python
# Correct
vbak_df = pd.read_sql(...)          # DataFrame of sales order headers
o2c_facts_df = transform_to_o2c_facts(...)  # Transformed fact data
customer_dim_df = pd.read_sql(...)  # Dimension table

# Incorrect (ambiguous)
vbak = pd.read_sql(...)             # Is this a DataFrame or dict?
o2c_facts = transform_to_o2c_facts(...)  # Unclear type
```

---

#### 2.4.2 Series Variables

**Pattern:** Suffix with `_series` to indicate pandas Series

```python
# Correct
revenue_series = vbak_df['netwr']  # Series of net revenues
days_to_cash_series = o2c_facts_df['days_to_cash']  # Series of metrics

# Incorrect
revenue = vbak_df['netwr']         # Could be Series or scalar
```

---

#### 2.4.3 Scalar & Dictionary Variables

**Pattern:** Use clear, descriptive names without suffix

```python
# Correct
total_revenue = 50000000  # Scalar
period_start = datetime(2026, 4, 1)  # Scalar
order_record = {'vbeln': '0013456789', 'kunnr': 'C1001', ...}  # Dictionary
reconciliation_result = {'matched': 100, 'unmatched': 2, 'variance': 500}  # Dict

# Incorrect
total_revenue_df = 50000000  # Misleading (not a DataFrame)
order_record_df = {...}     # Misleading (not a DataFrame)
```

---

## 3. Data Integrity Rules (Mandatory)

**Rule:** Every AI-generated data processing function must include explicit validation and error handling for these mandatory rules.

### 3.1 Sales Order Integrity

**Rule O2C-01:** Every sales order item must reference a valid customer, material, and plant.

```python
def validate_sales_order_integrity(vbap_df, customer_dim_df, product_dim_df, plant_dim_df):
    """
    Mandatory validation for O2C facts.
    Raises: ValueError if referential integrity violated.
    """
    errors = []
    
    # Check customer references
    invalid_customers = vbap_df[~vbap_df['kunnr'].isin(customer_dim_df['customer_id'])]
    if len(invalid_customers) > 0:
        errors.append(f"Invalid customers in {len(invalid_customers)} rows: {invalid_customers['kunnr'].unique()}")
    
    # Check product references
    invalid_products = vbap_df[~vbap_df['matnr'].isin(product_dim_df['material_code'])]
    if len(invalid_products) > 0:
        errors.append(f"Invalid products in {len(invalid_products)} rows: {invalid_products['matnr'].unique()}")
    
    # Check plant references (must be PL01 or PL02)
    valid_plants = {'PL01', 'PL02'}
    invalid_plants = vbap_df[~vbap_df['werks'].isin(valid_plants)]
    if len(invalid_plants) > 0:
        errors.append(f"Invalid plants in {len(invalid_plants)} rows: {invalid_plants['werks'].unique()}")
    
    # Check company code (must be NV01)
    if not all(vbap_df['bukrs'] == 'NV01'):
        errors.append("All rows must have bukrs = 'NV01'")
    
    if errors:
        raise ValueError("Sales Order Integrity Violations:\n" + "\n".join(errors))
    
    return True
```

---

### 3.2 GL Account Integrity

**Rule GL-01:** Every GL posting must reference a valid GL account from the chart of accounts.

```python
def validate_gl_account_integrity(acdoca_df, valid_gl_accounts):
    """
    Mandatory validation for GL facts.
    valid_gl_accounts: Set of 6-digit GL codes (e.g., {'600001', '600002', '700001', ...})
    Raises: ValueError if invalid GL accounts detected.
    """
    invalid_accounts = acdoca_df[~acdoca_df['gkont'].isin(valid_gl_accounts)]
    
    if len(invalid_accounts) > 0:
        raise ValueError(
            f"Invalid GL accounts in {len(invalid_accounts)} rows: "
            f"{invalid_accounts['gkont'].unique()}"
        )
    
    return True
```

---

### 3.3 Amount Integrity

**Rule AMT-01:** No negative amounts or quantities allowed (except GL documents with intentional reversals).

```python
def validate_no_negative_amounts(df, numeric_columns=['menge', 'netwr', 'dmbtr']):
    """
    Mandatory validation: No negative amounts/quantities.
    Exception: GL reversals (documented with "_REV" in reference).
    Raises: ValueError if invalid negatives found.
    """
    for col in numeric_columns:
        if col not in df.columns:
            continue
        
        negatives = df[df[col] < 0]
        
        # Allow GL reversals (reference field contains "REV" or "REVERSAL")
        if col == 'dmbtr' and 'xblnr' in df.columns:
            negatives = negatives[~negatives['xblnr'].str.contains('REV', case=False, na=False)]
        
        if len(negatives) > 0:
            raise ValueError(
                f"Invalid negative values in column '{col}': {len(negatives)} rows\n"
                f"{negatives.head(5)}"
            )
    
    return True
```

---

### 3.4 Date Sequence Integrity

**Rule DATE-01:** In the Order-to-Cash cycle, date sequence must be: order_date ≤ delivery_date ≤ invoice_date ≤ cash_date.

```python
def validate_o2c_date_sequence(o2c_df):
    """
    Mandatory validation: O2C dates must follow logical sequence.
    Raises: ValueError if sequence violated.
    """
    # Fill NaN dates with max date to avoid comparison issues
    o2c_check = o2c_df.copy()
    max_date = pd.Timestamp.max
    
    o2c_check['order_date'] = pd.to_datetime(o2c_check['order_date'])
    o2c_check['delivery_date'] = pd.to_datetime(o2c_check['delivery_date']).fillna(max_date)
    o2c_check['invoice_date'] = pd.to_datetime(o2c_check['invoice_date']).fillna(max_date)
    o2c_check['cash_date'] = pd.to_datetime(o2c_check['cash_date']).fillna(max_date)
    
    # Check sequence
    violations = o2c_check[
        ~((o2c_check['order_date'] <= o2c_check['delivery_date']) &
          (o2c_check['delivery_date'] <= o2c_check['invoice_date']) &
          (o2c_check['invoice_date'] <= o2c_check['cash_date']))
    ]
    
    if len(violations) > 0:
        raise ValueError(
            f"O2C date sequence violated in {len(violations)} rows:\n"
            f"{violations[['order_date', 'delivery_date', 'invoice_date', 'cash_date']].head(5)}"
        )
    
    return True
```

---

### 3.5 GL Balance Integrity

**Rule GL-02:** Total debits must equal total credits within rounding tolerance (±0.01 INR).

```python
def validate_gl_balance(acdoca_df, tolerance_inr=0.01):
    """
    Mandatory validation: GL must balance (total debits ≈ total credits).
    Raises: ValueError if imbalanced by more than tolerance.
    """
    total_debit = acdoca_df[acdoca_df['dmbtr'] > 0]['dmbtr'].sum()
    total_credit = acdoca_df[acdoca_df['dmbtr'] < 0]['dmbtr'].abs().sum()
    
    variance = abs(total_debit - total_credit)
    
    if variance > tolerance_inr:
        raise ValueError(
            f"GL Balance Violation: Debits ₹{total_debit:.2f}, "
            f"Credits ₹{total_credit:.2f}, Variance ₹{variance:.2f} "
            f"(Tolerance: ₹{tolerance_inr:.2f})"
        )
    
    return True
```

---

### 3.6 Inventory Integrity

**Rule INV-01:** Closing stock balance = Opening + Receipts − Issues. No stock should ever go negative.

```python
def validate_inventory_balance(inventory_df, tolerance=0.001):
    """
    Mandatory validation: Inventory balance equation must hold.
    closing_balance = opening_balance + receipts - issues
    Raises: ValueError if violated.
    """
    inventory_df = inventory_df.copy()
    
    # Calculate expected closing balance
    inventory_df['calculated_closing'] = (
        inventory_df['opening_balance_qty'] + 
        inventory_df['receipts_qty'] - 
        inventory_df['issues_qty']
    )
    
    # Compare with actual
    variance = (inventory_df['calculated_closing'] - inventory_df['closing_balance_qty']).abs()
    
    violations = inventory_df[variance > tolerance]
    
    if len(violations) > 0:
        raise ValueError(
            f"Inventory Balance Violations in {len(violations)} rows:\n"
            f"{violations[['calculated_closing', 'closing_balance_qty', 'variance']].head(5)}"
        )
    
    # Check for negative balances
    negatives = inventory_df[inventory_df['closing_balance_qty'] < 0]
    if len(negatives) > 0:
        raise ValueError(f"Negative stock in {len(negatives)} locations (impossible without correction)")
    
    return True
```

---

## 4. Error Handling & Logging (Mandatory)

**Rule:** Every data processing function must include:
1. Try-except blocks for external system calls (SAP, database)
2. Structured logging at INFO, WARNING, and ERROR levels
3. Graceful error recovery with retry logic (for network failures)
4. Detailed error messages with context

### 4.1 Logging Template

```python
import logging
from datetime import datetime

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('/var/log/novastream_etl.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def extract_with_error_handling(sap_connection, table_name, extract_date):
    """
    Example: Extract from SAP with error handling and logging.
    """
    logger.info(f"Starting extraction of {table_name} from {extract_date}")
    
    try:
        result = sap_connection.fetch_table(
            table_name, 
            where=f"posting_date >= '{extract_date}'"
        )
        
        logger.info(f"✓ Extracted {len(result)} rows from {table_name}")
        return result
    
    except ConnectionError as e:
        logger.error(f"✗ SAP connection error: {e}", exc_info=True)
        # Implement retry logic
        logger.info("Retrying after 30 seconds...")
        time.sleep(30)
        return extract_with_error_handling(sap_connection, table_name, extract_date)
    
    except Exception as e:
        logger.critical(f"✗ Unexpected error extracting {table_name}: {e}", exc_info=True)
        raise
```

---

### 4.2 Transaction Logging (Data Lineage)

**Rule:** Track every row's journey through the ETL pipeline for audit trails.

```python
def load_with_lineage_tracking(df, target_table, engine, batch_id):
    """
    Load data to DW with lineage tracking.
    Adds etl_load_date, etl_batch_id columns.
    """
    logger.info(f"Loading {len(df)} rows to {target_table} (batch {batch_id})")
    
    df_load = df.copy()
    df_load['etl_load_date'] = datetime.now()
    df_load['etl_batch_id'] = batch_id
    
    try:
        df_load.to_sql(target_table, con=engine, if_exists='append', index=False, chunksize=1000)
        logger.info(f"✓ Loaded {len(df_load)} rows to {target_table}")
    
    except Exception as e:
        logger.error(f"✗ Load failed for {target_table}: {e}", exc_info=True)
        raise
```

---

## 5. Code Quality Standards (Mandatory)

### 5.1 Type Hints

**Rule:** All function signatures must include type hints for parameters and return values.

```python
# Correct
from typing import Tuple, List, Dict, Optional
import pandas as pd
from datetime import datetime

def extract_sales_orders(
    bukrs: str = 'NV01',
    extract_date: datetime = None,
    max_rows: Optional[int] = None
) -> pd.DataFrame:
    """
    Extract sales orders from SAP.
    
    Args:
        bukrs: Company code (default NV01)
        extract_date: Extract orders from this date onward
        max_rows: Limit result set (None = no limit)
    
    Returns:
        DataFrame with VBAK/VBAP data
    
    Raises:
        ValueError: If bukrs is not valid
        ConnectionError: If SAP connection fails
    """
    pass

def transform_to_facts(
    vbak_df: pd.DataFrame,
    vbap_df: pd.DataFrame,
    likp_df: pd.DataFrame
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Transform raw sales data to O2C facts.
    
    Returns:
        (facts_df, metrics_dict) where metrics_dict contains:
            - rows_processed: int
            - rows_skipped: int
            - validation_errors: int
    """
    pass

# Incorrect (no type hints)
def extract_sales_orders(bukrs, extract_date=None, max_rows=None):
    pass
```

---

### 5.2 Docstrings

**Rule:** All functions must include comprehensive docstrings following NumPy/Google style.

```python
def calculate_gross_margin(
    revenue_amount: float,
    cogs_amount: float,
    currency: str = 'INR'
) -> Dict[str, float]:
    """
    Calculate gross profit and margin percentage.
    
    This function computes profitability metrics commonly used in financial analysis.
    It supports multiple currencies and includes validation for currency support.
    
    Parameters
    ----------
    revenue_amount : float
        Total revenue in local currency (e.g., ₹1,062,000.00).
    cogs_amount : float
        Cost of goods sold in same currency.
    currency : str, optional
        Currency code (default: 'INR'). Must be 'INR' for NovaStream.
    
    Returns
    -------
    Dict[str, float]
        Dictionary containing:
        - 'gross_profit': float = revenue - cogs
        - 'gross_margin_pct': float = (gross_profit / revenue) * 100
        - 'cogs_pct': float = (cogs / revenue) * 100
    
    Raises
    ------
    ValueError
        If revenue_amount <= 0 or cogs_amount < 0 or currency != 'INR'.
    
    Examples
    --------
    >>> result = calculate_gross_margin(1062000.00, 581000.00, 'INR')
    >>> result['gross_margin_pct']
    45.30
    
    Notes
    -----
    - All amounts must be positive (except COGS can equal 0 for free items)
    - Rounding follows Indian accounting: 2 decimal places for ₹
    - NovaStream standard target margin: 40-50% for Electronics, 35-45% for Accessories
    """
    if revenue_amount <= 0:
        raise ValueError(f"Revenue must be positive, got {revenue_amount}")
    if cogs_amount < 0:
        raise ValueError(f"COGS cannot be negative, got {cogs_amount}")
    if currency != 'INR':
        raise ValueError(f"Unsupported currency {currency}, expected INR")
    
    gross_profit = revenue_amount - cogs_amount
    gross_margin_pct = (gross_profit / revenue_amount) * 100
    cogs_pct = (cogs_amount / revenue_amount) * 100
    
    return {
        'gross_profit': round(gross_profit, 2),
        'gross_margin_pct': round(gross_margin_pct, 2),
        'cogs_pct': round(cogs_pct, 2)
    }
```

---

### 5.3 Unit Tests

**Rule:** All transformation and calculation functions must have corresponding unit tests.

```python
import pytest
import pandas as pd
from scripts.transform import calculate_gross_margin, validate_sales_order_integrity

def test_calculate_gross_margin_standard_case():
    """Test gross margin calculation with typical values."""
    result = calculate_gross_margin(1062000.00, 581000.00, 'INR')
    
    assert result['gross_profit'] == 481000.00
    assert result['gross_margin_pct'] == 45.30
    assert result['cogs_pct'] == 54.70

def test_calculate_gross_margin_zero_revenue():
    """Test that zero revenue raises ValueError."""
    with pytest.raises(ValueError, match="Revenue must be positive"):
        calculate_gross_margin(0, 100, 'INR')

def test_calculate_gross_margin_negative_cogs():
    """Test that negative COGS raises ValueError."""
    with pytest.raises(ValueError, match="COGS cannot be negative"):
        calculate_gross_margin(1000, -100, 'INR')

def test_calculate_gross_margin_unsupported_currency():
    """Test that non-INR currency raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported currency"):
        calculate_gross_margin(1000, 500, 'USD')

def test_validate_sales_order_integrity_valid_data():
    """Test validation passes with correct customer/product/plant references."""
    vbap_df = pd.DataFrame({
        'vbeln': ['0013456789'],
        'kunnr': ['C1001'],
        'matnr': ['NSTV-55'],
        'werks': ['PL01'],
        'bukrs': ['NV01']
    })
    
    customer_dim = pd.DataFrame({'customer_id': ['C1001']})
    product_dim = pd.DataFrame({'material_code': ['NSTV-55']})
    plant_dim = pd.DataFrame({'plant_code': ['PL01']})
    
    assert validate_sales_order_integrity(vbap_df, customer_dim, product_dim, plant_dim) == True

def test_validate_sales_order_integrity_invalid_customer():
    """Test validation fails with invalid customer reference."""
    vbap_df = pd.DataFrame({
        'vbeln': ['0013456789'],
        'kunnr': ['C9999'],  # Invalid
        'matnr': ['NSTV-55'],
        'werks': ['PL01'],
        'bukrs': ['NV01']
    })
    
    customer_dim = pd.DataFrame({'customer_id': ['C1001']})  # Only C1001 valid
    product_dim = pd.DataFrame({'material_code': ['NSTV-55']})
    plant_dim = pd.DataFrame({'plant_code': ['PL01']})
    
    with pytest.raises(ValueError, match="Invalid customers"):
        validate_sales_order_integrity(vbap_df, customer_dim, product_dim, plant_dim)
```

---

## 6. Database Schema Constraints

**Rule:** All DDL (table creation) must include constraints enforcing data integrity.

```sql
-- Example: O2C Fact Table DDL with constraints
CREATE TABLE fct_o2c_transactions (
    o2c_fact_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- Foreign Keys (referential integrity)
    customer_key INT NOT NULL REFERENCES dim_customer(customer_key),
    product_key INT NOT NULL REFERENCES dim_product(product_key),
    plant_key INT NOT NULL REFERENCES dim_plant(plant_key),
    sales_org_key INT NOT NULL REFERENCES dim_sales_org(sales_org_key),
    
    -- Mandatory fields
    order_id VARCHAR(10) NOT NULL,
    order_item_id VARCHAR(5) NOT NULL,
    order_date DATE NOT NULL,
    order_amount_local DECIMAL(15,2) NOT NULL,
    order_qty DECIMAL(13,3) NOT NULL,
    
    -- Data validation constraints
    CONSTRAINT chk_order_amount_positive CHECK (order_amount_local >= 0),
    CONSTRAINT chk_order_qty_positive CHECK (order_qty > 0),
    CONSTRAINT chk_company_code CHECK (company_code = 'NV01'),
    CONSTRAINT chk_plant_valid CHECK (plant_id IN ('PL01', 'PL02')),
    
    -- Unique constraints
    UNIQUE KEY uk_o2c_order_item (order_id, order_item_id),
    
    -- Indexes for query performance
    INDEX idx_customer (customer_key),
    INDEX idx_product (product_key),
    INDEX idx_order_date (order_date)
);
```

---

## 7. Performance & Optimization Guidelines

### 7.1 Batch Processing

**Rule:** Always use chunked/batch processing for large DataFrames to avoid memory overflow.

```python
# Correct: Batch processing
def load_large_dataset(df, table_name, engine, batch_size=10000):
    """Load large DataFrame in chunks."""
    logger.info(f"Loading {len(df)} rows in batches of {batch_size}")
    
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]
        batch.to_sql(table_name, con=engine, if_exists='append', index=False)
        logger.info(f"Loaded batch {i//batch_size + 1}/{(len(df)-1)//batch_size + 1}")

# Incorrect: Single insert (memory-intensive, slow)
def load_large_dataset_bad(df, table_name, engine):
    df.to_sql(table_name, con=engine, if_exists='append', index=False)  # Danger!
```

---

### 7.2 Indexing

**Rule:** Create indexes on frequently queried dimensions and date columns.

```python
# Create indexes in database
def create_indexes(engine):
    """Create indexes for query performance."""
    index_queries = [
        "CREATE INDEX idx_o2c_customer ON fct_o2c_transactions(customer_key);",
        "CREATE INDEX idx_o2c_product ON fct_o2c_transactions(product_key);",
        "CREATE INDEX idx_o2c_date ON fct_o2c_transactions(date_key_order);",
        "CREATE INDEX idx_gl_account ON fct_gl_reconciliation(gl_account_key);",
        "CREATE INDEX idx_inv_material ON fct_inventory_facts(material_key, plant_key);",
    ]
    
    with engine.connect() as conn:
        for query in index_queries:
            conn.execute(text(query))
            logger.info(f"Created index: {query}")
        conn.commit()
```

---

## 8. Configuration & Environment Management

**Rule:** Use environment variables and configuration files (not hardcoded credentials).

```python
# Correct: Use environment variables
import os
from dotenv import load_dotenv

load_dotenv('/etc/novastream/.env')

SAP_CONFIG = {
    'ashost': os.getenv('SAP_HOST', 'sap.prod.local'),
    'sysnr': os.getenv('SAP_SYSNR', '00'),
    'client': os.getenv('SAP_CLIENT', '100'),
    'user': os.getenv('SAP_USER'),  # Must be set in .env
    'passwd': os.getenv('SAP_PASSWD'),  # Must be set in .env (not in code!)
}

DWH_CONFIG = {
    'db_type': os.getenv('DWH_TYPE', 'postgresql'),  # postgresql or sqlite
    'host': os.getenv('DWH_HOST', 'localhost'),
    'port': int(os.getenv('DWH_PORT', '5432')),
    'database': os.getenv('DWH_DB', 'novastream_dw'),
    'user': os.getenv('DWH_USER'),
    'password': os.getenv('DWH_PASSWD'),
}

# Construct connection string
DWH_URI = (
    f"{DWH_CONFIG['db_type']}://"
    f"{DWH_CONFIG['user']}:{DWH_CONFIG['password']}@"
    f"{DWH_CONFIG['host']}:{DWH_CONFIG['port']}/"
    f"{DWH_CONFIG['database']}"
)

# Incorrect: Hardcoded credentials (NEVER DO THIS!)
# DWH_URI = "postgresql://analytics:password123@localhost/dw"  # ❌ WRONG!
```

---

## 9. Checklist for AI Agents

**Before generating any code, validate:**

- [ ] **Naming:** All SAP variables use SAP-standard abbreviations (`bukrs`, `werks`, `matnr`, `kunnr`, etc.)
- [ ] **Type Hints:** All function signatures have type hints for parameters & return values
- [ ] **Docstrings:** All functions have comprehensive NumPy/Google-style docstrings
- [ ] **Error Handling:** Try-except blocks for all external system calls with logging
- [ ] **Data Validation:** Mandatory rules enforced (referential integrity, no negatives, date sequences, GL balance)
- [ ] **Logging:** INFO, WARNING, ERROR level logs with context
- [ ] **Tests:** Unit tests for all transformation & validation functions
- [ ] **Database Constraints:** DDL includes NOT NULL, CHECK, UNIQUE, FK constraints
- [ ] **Batch Processing:** Large datasets processed in chunks (batch_size ≥ 1000)
- [ ] **Configuration:** No hardcoded credentials; uses environment variables
- [ ] **Comments:** Complex logic documented inline
- [ ] **Performance:** Indexes created on frequently queried columns (customer_key, product_key, date keys)

---

## 10. Example: Complete AI-Generated Function

```python
# Example function generated according to all rules above

def extract_and_validate_sales_orders(
    bukrs: str = 'NV01',
    extract_date: Optional[datetime] = None,
    max_retries: int = 3
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Extract sales orders from SAP and perform validation.
    
    Extracts VBAK/VBAP (Sales Order Header/Item) data from SAP ERP for the
    specified company code. Validates customer, product, plant references.
    Returns both validated data and validation metrics.
    
    Parameters
    ----------
    bukrs : str, optional
        Company code (default: 'NV01'). Must be 'NV01' for NovaStream.
    extract_date : Optional[datetime], optional
        Extract orders from this date onward. If None, extracts from prior day.
    max_retries : int, optional
        Number of retry attempts for SAP connection (default: 3).
    
    Returns
    -------
    Tuple[pd.DataFrame, Dict[str, int]]
        - DataFrame: Valid sales order data (VBAK + VBAP merged)
        - Dict: Validation metrics
            - 'rows_extracted': int
            - 'rows_valid': int
            - 'rows_invalid': int
            - 'invalid_customers': int
            - 'invalid_products': int
            - 'invalid_plants': int
    
    Raises
    ------
    ValueError
        If bukrs is not 'NV01' or if >5% of rows are invalid.
    ConnectionError
        If SAP connection fails after max_retries attempts.
    
    Examples
    --------
    >>> vbak_df, metrics = extract_and_validate_sales_orders(
    ...     bukrs='NV01',
    ...     extract_date=datetime(2026, 4, 15)
    ... )
    >>> print(f"Valid rows: {metrics['rows_valid']}")
    Valid rows: 250
    
    Notes
    -----
    - Extraction occurs daily at 02:00 AM IST (off-peak)
    - Includes prior day + current day for reprocessing
    - Returns only complete order-item pairs (no orphaned items)
    """
    
    logger = logging.getLogger(__name__)
    logger.info(f"extract_and_validate_sales_orders(bukrs={bukrs}, extract_date={extract_date})")
    
    # Validate input
    if bukrs != 'NV01':
        raise ValueError(f"Only bukrs='NV01' supported, got {bukrs}")
    
    if extract_date is None:
        extract_date = datetime.now().date() - timedelta(days=1)
    
    logger.info(f"Extracting sales orders from {extract_date} for bukrs={bukrs}")
    
    # Attempt extraction with retry logic
    vbak_df = None
    for attempt in range(max_retries):
        try:
            # Connect to SAP
            sap = SAPConnection(config=SAP_CONFIG)
            
            # Query VBAK + VBAP
            query_vbak = f"""
            SELECT vbeln, erdat, vkorg, vtweg, spart, kunnr, netwr
            FROM vbak
            WHERE bukrs = '{bukrs}'
              AND erdat >= '{extract_date}'
            """
            
            query_vbap = f"""
            SELECT vbeln, posnr, matnr, menge, meins, werks, arktx
            FROM vbap
            WHERE bukrs = '{bukrs}'
              AND erdat >= '{extract_date}'
            """
            
            vbak_df = pd.read_sql(query_vbak, sap.connection())
            vbap_df = pd.read_sql(query_vbap, sap.connection())
            
            logger.info(f"✓ Extracted {len(vbak_df)} VBAK + {len(vbap_df)} VBAP rows")
            break
        
        except ConnectionError as e:
            logger.warning(f"⚠ SAP connection failed (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(30)  # Wait 30 seconds before retry
            else:
                logger.critical(f"✗ SAP connection failed after {max_retries} attempts")
                raise ConnectionError(f"Unable to connect to SAP after {max_retries} retries") from e
    
    # Merge VBAK + VBAP
    sales_df = vbak_df.merge(vbap_df, on='vbeln', how='inner')
    rows_extracted = len(sales_df)
    logger.info(f"Merged VBAK/VBAP: {rows_extracted} rows")
    
    # Load dimension tables for validation
    customer_dim_df = pd.read_sql(
        "SELECT DISTINCT customer_id FROM dim_customer WHERE is_current = TRUE",
        engine
    )
    product_dim_df = pd.read_sql(
        "SELECT DISTINCT material_code FROM dim_product WHERE is_current = TRUE",
        engine
    )
    
    # Validate customer references
    invalid_customers = sales_df[~sales_df['kunnr'].isin(customer_dim_df['customer_id'])]
    if len(invalid_customers) > 0:
        logger.warning(f"⚠ Found {len(invalid_customers)} invalid customer references: {invalid_customers['kunnr'].unique()}")
    
    # Validate product references
    invalid_products = sales_df[~sales_df['matnr'].isin(product_dim_df['material_code'])]
    if len(invalid_products) > 0:
        logger.warning(f"⚠ Found {len(invalid_products)} invalid product references: {invalid_products['matnr'].unique()}")
    
    # Validate plants
    valid_plants = {'PL01', 'PL02'}
    invalid_plants = sales_df[~sales_df['werks'].isin(valid_plants)]
    if len(invalid_plants) > 0:
        logger.warning(f"⚠ Found {len(invalid_plants)} invalid plant codes: {invalid_plants['werks'].unique()}")
    
    # Remove invalid rows
    sales_df_valid = sales_df[
        (sales_df['kunnr'].isin(customer_dim_df['customer_id'])) &
        (sales_df['matnr'].isin(product_dim_df['material_code'])) &
        (sales_df['werks'].isin(valid_plants))
    ]
    
    rows_valid = len(sales_df_valid)
    rows_invalid = rows_extracted - rows_valid
    invalid_pct = (rows_invalid / rows_extracted) * 100 if rows_extracted > 0 else 0
    
    logger.info(f"✓ Validation complete: {rows_valid} valid, {rows_invalid} invalid ({invalid_pct:.1f}%)")
    
    # Check if error threshold exceeded
    if invalid_pct > 5:
        logger.error(f"✗ Invalid row percentage {invalid_pct:.1f}% exceeds SLA of 5%")
        raise ValueError(f"Data quality threshold exceeded: {invalid_pct:.1f}% invalid rows")
    
    # Compile metrics
    metrics = {
        'rows_extracted': rows_extracted,
        'rows_valid': rows_valid,
        'rows_invalid': rows_invalid,
        'invalid_customers': len(invalid_customers),
        'invalid_products': len(invalid_products),
        'invalid_plants': len(invalid_plants),
    }
    
    logger.info(f"extract_and_validate_sales_orders completed: {metrics}")
    return sales_df_valid, metrics


# Unit test for above function
def test_extract_and_validate_sales_orders():
    """Test extraction and validation of sales orders."""
    
    # Create test data
    test_vbak = pd.DataFrame({
        'vbeln': ['0013456789', '0013456790'],
        'erdat': ['2026-04-15', '2026-04-15'],
        'kunnr': ['C1001', 'C9999'],  # C9999 is invalid
        'netwr': [1062000, 500000],
        'bukrs': ['NV01', 'NV01'],
    })
    
    # Mock SAP connection to return test data
    # (In real code, this would be done with unittest.mock)
    
    # Call function (would fail with mock setup)
    # vbak_df, metrics = extract_and_validate_sales_orders(extract_date=datetime(2026, 4, 15))
    
    # Assert metrics
    # assert metrics['rows_extracted'] == 2
    # assert metrics['rows_valid'] == 1  # C1001 valid, C9999 invalid
    # assert metrics['invalid_customers'] == 1
```

---

## 11. Approval & Governance

| Role | Responsibility | Contact |
|------|-----------------|---------|
| Lead Data Engineer | Code review, rule enforcement | [Name] |
| Analytics Architect | SRS compliance, schema design | [Name] |
| Database Admin | Index design, performance monitoring | [Name] |
| SAP Admin | SAP connectivity, data extraction strategy | [Name] |
| QA Lead | Test plan, data validation | [Name] |

---

**End of ANALYTICS_AGENTS.md**

*This document is the source of truth for all code generation related to the NovaStream Analytics platform. Any deviations must be approved by the Lead Data Engineer.*
