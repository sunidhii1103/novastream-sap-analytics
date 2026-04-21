# Analytics Product Requirements Document (PRD)
## NovaStream Electronics SAP Data Analytics Platform

**Project:** NovaStream Electronics Data Analytics Initiative  
**Version:** 1.0  
**Date:** April 21, 2026  
**Organization:** NovaStream Electronics Pvt. Ltd.  
**Classification:** Technical Design Document  

---

## 1. Executive Summary

NovaStream Electronics Pvt. Ltd. operates three integrated SAP modules (FI, MM, SD) across a distributed organizational structure comprising Company Code NV01, Manufacturing Plant PL01 (Bhubaneswar), and Distribution Hub PL02 (Pune). While the enterprise structure is now configured, transactional data remains fragmented across module-specific views. This PRD defines a unified analytics platform that synthesizes Financial Accounting (FI), Materials Management (MM), and Sales & Distribution (SD) data into a cohesive business intelligence layer, enabling real-time visibility into Order-to-Cash (O2C) cycles and Month-End Financial Close (R2R) processes.

---

## 2. Business Problem Statement

### 2.1 Current State Challenges

Despite SAP Enterprise Structure implementation, NovaStream Electronics faces three critical analytics gaps:

1. **Siloed Module Visibility:** Sales transactions exist in SD tables (VBAK, VBAP), inventory movements in MM tables (MKPF, MSEG), and financial postings in FI tables (ACDOCA). Finance Controllers cannot trace a revenue entry back to the underlying sales order; Supply Chain Analysts cannot correlate inventory positions with customer demand; Sales Managers lack real-time profitability by customer/region.

2. **Delayed Reporting Cycles:** Month-End Financial Close (R2R) requires manual reconciliation across three modules. The absence of a unified data layer means Finance Controllers spend 40% of close time reconciling GL balances with sub-ledger documents (G/L 600001 Revenue vs. VBAK Sales Orders, G/L 200001 Inventory vs. MBLK Material Documents). This delays regulatory reporting and management decision-making.

3. **Limited Decision Support:** There is no single source of truth for:
   - Customer-level profitability (which customers/channels drive margin?)
   - Regional performance (Bhubaneswar manufacturing vs. Pune distribution?)
   - Operational KPIs (Days Sales Outstanding, Cash Conversion Cycle, Inventory Turnover)
   - Variance analysis (actual vs. budget revenue by sales area)

### 2.2 Business Objectives

This analytics platform will:
- **Enable Real-Time O2C Visibility:** Link every sales order (VBAK) through delivery (LIKP) to invoice (VBRK) to cash receipt (BSAK), displaying the cash conversion timeline with customer-level precision.
- **Accelerate Month-End Close:** Provide automated reconciliation dashboards that verify GL balances against SD revenue, MM costs, and FI accruals, reducing close time from 7 days to 2–3 days.
- **Support Operational Decision-Making:** Deliver KPIs aligned to three distinct personas (Sales Manager, Finance Controller, Supply Chain Analyst), enabling daily decisions without manual reporting effort.
- **Establish Audit Trail:** Maintain transparent traceability from transaction origin (VA01 Sales Order) through posting entry (FB01 GL Entry) to financial statement impact.

---

## 3. Target Personas and Use Cases

### 3.1 Persona 1: Sales Manager (NV10 Sales Organization)

**Role:** Responsible for revenue target achievement, customer relationship management, and sales forecast accuracy for Sales Organization NV10 (covering Distribution Channels 10/Wholesale and 20/Retail, Divisions EL/Electronics and AC/Accessories).

**Key Questions:**
- How much revenue have we booked this month by sales area (NV10/10/EL vs. NV10/20/AC)?
- Which customers/regions are driving profitability? (Wholesale network in Delhi vs. Retail in Bangalore)
- What is our order fulfillment rate? (Orders created in VA01 vs. goods issued in VL02N)
- Are we hitting monthly/quarterly revenue targets by division (Electronics vs. Accessories)?

**Required Outputs:**
- Revenue Dashboard: Daily revenue tracked by Sales Area (4 combinations), Distribution Channel, Division, and Customer.
- Customer Profitability Matrix: Gross Margin %, Order Frequency, and Days Sales Outstanding (DSO) by customer.
- Fulfillment Pipeline: Order book visibility from VBAK (created), VBAP (open), VBRK (billed), to BSAK (cash received).

---

### 3.2 Persona 2: Finance Controller (Company Code NV01)

**Role:** Responsible for accurate and timely financial reporting, regulatory compliance, month-end close, and variance analysis for Company Code NV01 (legal entity covering both plants and all sales channels).

**Key Questions:**
- What is the reconciliation status between GL accounts and source documents (SD, MM)?
- Is revenue recognized according to GST compliance rules?
- What is the impact of inventory valuation changes on Cost of Goods Sold (G/L 700001)?
- Are all FI-MM-SD transactions properly interlinked without gaps?

**Required Outputs:**
- GL Reconciliation Dashboard: Real-time matching of GL balances (ACDOCA) with source documents (VBAK revenue, MKPF stock movements, MBLK material documents).
- Month-End Close Checklist: Automated validation of accruals, cutoffs, and period closes with drill-down to supporting documents.
- Variance Analysis: Actual GL vs. Budget (if available), broken down by cost center, cost object (customer, product), and transaction type.

---

### 3.3 Persona 3: Supply Chain Analyst (Plants PL01, PL02)

**Role:** Responsible for inventory optimization, material flow efficiency, and procurement planning across Plants PL01 (manufacturing) and PL02 (distribution).

**Key Questions:**
- What is the current stock position by plant, storage location, and material?
- How quickly is inventory turning (inventory days for each finished product)?
- Are safety stock levels appropriate given customer demand volatility?
- What is the supply chain lead time from raw material (RM-PCB-01) through manufacturing to finished goods (NSTV-55)?

**Required Outputs:**
- Inventory Position Dashboard: Stock levels by Plant (PL01, PL02), Storage Location (SL01–SL05), and Material, updated in real-time from MBLK (goods movements).
- Inventory Health Scorecard: Inventory Turnover Ratio, Days Inventory Outstanding (DIO), Obsolescence Risk (aged stock), and safety stock variance.
- Procurement Pipeline: Open POs from purchasing (EKKO), GRN status (MSEG), and cost variance from planned vs. actual receipt.

---

## 4. Core Analytics Features

### 4.1 Feature 1: Order-to-Cash (O2C) Cycle Tracking

**Description:** End-to-end visibility of customer order lifecycle from initiation through cash receipt.

**Data Flow:**
1. **Order Creation (SD Module):** VBAK (Sales Order Header) + VBAP (Sales Order Item) capture order date, customer, material, quantity, plant, delivery date.
2. **Delivery & Inventory Depletion (MM Module):** LIKP (Outbound Delivery Header) + LIPS (Delivery Item) + MSEG (Material Document) track goods issue from storage location, stock reduction, and COGS posting to G/L 700001.
3. **Billing & Revenue Recognition (SD/FI Module):** VBRK (Billing Document Header) + VBRP (Billing Item) + ACDOCA (GL Document) record invoice, revenue posting to G/L 600001, and GST liability to G/L 800001.
4. **Cash Application (FI Module):** BSAK (GL Item Clearing) records customer payment matching against BSAD (GL Item Clearing Line), clearing AR balance (G/L 300001).

**Analytics Deliverables:**
- **O2C Pipeline Dashboard:** Visual funnel showing % of orders progressing through each stage (Created → Confirmed → Picked → Billed → Paid).
- **Days to Cash Report:** Average time from order creation to cash receipt, segmented by customer, sales area, and division. Highlights DSO and cash conversion cycle efficiency.
- **Order Exception Report:** Orders stuck in any stage (e.g., created but not delivered after 5 days, billed but unpaid after 30 days).

### 4.2 Feature 2: Month-End Financial Close (R2R) Visibility

**Description:** Automated reconciliation and validation of financial period close across all three modules.

**Data Flow:**
1. **GL Balance Snapshot (FI):** Extract ACDOCA balances for all 17 G/L accounts (Balance Sheet and P&L) at period end.
2. **SD Revenue Reconciliation:** Sum VBRK/VBRP billing items for the period, grouped by GL revenue account (600001, 600002), and match to GL posting.
3. **MM Cost Reconciliation:** Sum MSEG COGS postings for goods issued, match to GL account 700001, validate against standard cost or average cost configured in MARA.
4. **Inventory Variance:** Compare GL balance (200001 Finished Goods) to sum of physical stock from MBLK by storage location, identify discrepancies.
5. **AR Reconciliation:** Total VBRK billings less BSAK payments, match to GL 300001 AR balance.

**Analytics Deliverables:**
- **GL Reconciliation Report:** Three-way match (GL balance ↔ SD documents ↔ MM documents) with exception flagging.
- **Close Readiness Dashboard:** Checklist of close activities (AR aging review, inventory count reconciliation, accrual validation) with completion status.
- **Period Close Variance Report:** Variance between expected and actual GL balances by account, with drill-down to source transaction.

### 4.3 Feature 3: Profitability & Margin Analysis

**Description:** Multi-dimensional profitability analysis enabling cost management and pricing strategy decisions.

**Data Dimensions:**
- By Customer (C1001, C1002, C1003, C1004, C1005)
- By Sales Area (NV10/10/EL, NV10/10/AC, NV10/20/EL, NV10/20/AC)
- By Product/Material (NSTV-55, NASP-01, NASP-02, NSTV-43, RM-PCB-01, etc.)
- By Plant (PL01, PL02)
- By Period (daily, weekly, monthly, yearly)

**Calculations:**
- **Gross Margin %** = (Revenue [G/L 600001 + 600002] − COGS [G/L 700001]) / Revenue
- **Contribution Margin** = Gross Margin − Logistics Cost (if tracked; placeholder in initial phase)
- **Net Margin** = (Revenue − COGS − Overhead allocation) / Revenue

**Analytics Deliverables:**
- **Profitability Heatmap:** Gross margin % by Customer × Product matrix, color-coded to highlight high-margin and loss-making combinations.
- **Channel Comparison:** Wholesale (DC 10) vs. Retail (DC 20) margin performance, identifying pricing or cost gaps.
- **Product Mix Analysis:** Revenue contribution and margin by division (Electronics EL vs. Accessories AC), guiding product strategy.

### 4.4 Feature 4: Inventory & Supply Chain Health

**Description:** Real-time inventory monitoring and supply chain performance metrics.

**Key Metrics:**
- **Inventory Turnover Ratio** = COGS / Average Inventory (calculated monthly)
- **Days Inventory Outstanding (DIO)** = 365 / Turnover Ratio (days products sit before sale)
- **Stock-to-Sales Ratio** = Current Inventory / Monthly Average Sales (months of stock on hand)
- **Safety Stock Variance** = Current Stock − (Average Daily Demand × Lead Time) (identifies over/under stocking)

**Analytics Deliverables:**
- **Inventory Position Report:** Current stock by Plant, Storage Location, and Material, flagging critical, excess, and obsolete stock.
- **Inventory Health Scorecard:** Turnover, DIO, and cash tied up by product line and plant.
- **Supply Chain Risk Dashboard:** Lead time tracking, supplier performance (if extended), and procurement cycle time.

---

## 5. Data Architecture Overview

### 5.1 Source System: SAP ERP (Transactional)

**Scope:** FI, MM, SD modules under Company Code NV01, Plants PL01/PL02, Sales Organization NV10.

**Primary Tables:**

| Module | Table | Description | Key Fields |
|--------|-------|-------------|-----------|
| SD | VBAK | Sales Order Header | VBELN (Order #), KUNNR (Customer), NETWR (Net Amount), ERDAT (Create Date) |
| SD | VBAP | Sales Order Item | VBELN, POSNR (Item), MATNR (Material), MENGE (Qty), ARKTX (Description) |
| SD | LIKP | Outbound Delivery Header | VBELN, LIKP# (Delivery), WBSTK (Goods Issue Date) |
| SD | LIPS | Outbound Delivery Item | LIKP#, POSNR, MATNR, LFIMG (Delivery Qty) |
| SD | VBRK | Billing Document Header | VBELN, VBRK# (Invoice), FKDAT (Billing Date), NETWR (Invoice Amount) |
| SD | VBRP | Billing Document Item | VBRK#, POSNR, MATNR, FKIMG (Billing Qty), NETWR (Item Revenue) |
| MM | MARA | Material Master | MATNR, MAKTX (Description), MTART (Type: FERT/ROH), MEINS (Unit) |
| MM | MBLK | Material Document Header | MKPF# (Doc #), BUDAT (Posting Date), VBELN (Ref. Order) |
| MM | MSEG | Material Document Item | MKPF#, POSNR, MATNR, MENGE (Qty), WERKS (Plant), LGORT (Storage Location) |
| MM | MARC | Plant-Material Link | MATNR, WERKS, PSTAT (Status), EKGRP (Purchasing Group) |
| FI | ACDOCA | GL Document (Line Item) | BELNR (GL Doc #), BUKRS (Company Code), GKONT (GL Account), DMBTR (Amount), BUDAT (Posting Date) |
| FI | BSAK | GL Item Clearing | BUKRS, BELNR (AR Doc), GJAHR (Fiscal Year), BUSCHL (Clearing Doc) |
| MM | KNA1 | Customer Master (linked from SD) | KUNNR (Customer #), NAME1 (Name), LAND1 (Country), TCODE (Tax Code) |

### 5.2 Integration Points (Where O2C Data Flows)

| Step | Source Table | Target Table | Field Mapping | Business Rule |
|------|-------------|-------------|-------------|---|
| 1: Order Created | VBAK | (SD staging) | VBELN → Order ID | Every sales order must reference valid KUNNR, MATNR, WERKS (plant) |
| 2: Goods Issued | MSEG | VBAK/ACDOCA | VBELN (reference) | Goods issue automatically posts COGS (G/L 700001) debit, Inventory (G/L 200001) credit |
| 3: Invoice Created | VBRK/VBRP | ACDOCA | VBELN (reference) | Invoice posting debits AR (G/L 300001), credits Revenue (G/L 600001), posts GST (G/L 800001) |
| 4: Payment Received | BSAK | ACDOCA/VBAK | BELNR (match) | Payment clears AR, reducing DSO, improving cash position |

---

## 6. Success Metrics & KPIs

### 6.1 Sales Manager KPIs

| KPI | Formula | Target | Reporting Frequency |
|-----|---------|--------|-------------------|
| Monthly Revenue | Sum(VBRK.NETWR) by Sales Area | ₹1.5–2.5 Cr (per division) | Daily |
| Order Fulfillment Rate | Count(VL02N) / Count(VBAK) | >90% | Weekly |
| Days Sales Outstanding (DSO) | Sum(AR) / (Monthly Revenue / 30) | <30 days | Weekly |
| Customer Acquisition Cost | (Sales Expenses) / New Customers | <5% of LTV | Monthly |
| Revenue by Channel | Wholesale vs. Retail breakdown | 60% Wholesale / 40% Retail (target) | Weekly |

### 6.2 Finance Controller KPIs

| KPI | Formula | Target | Reporting Frequency |
|-----|---------|--------|-------------------|
| GL Reconciliation Rate | (Matched Items / Total Items) × 100 | 100% | Daily at period-end |
| Close Cycle Time | Days from period-end to GL sign-off | <3 days | Monthly |
| Variance % | (Actual − Budget) / Budget × 100 | <5% for all material accounts | Monthly |
| COGS as % of Revenue | (G/L 700001) / (G/L 600001 + 600002) | 55–65% (industry standard) | Monthly |
| AR Aging >60 Days | Count(overdue AR) / Total AR | <10% of total | Weekly |

### 6.3 Supply Chain Analyst KPIs

| KPI | Formula | Target | Reporting Frequency |
|-----|---------|--------|-------------------|
| Inventory Turnover | COGS / Avg Inventory | >4× per year | Monthly |
| Days Inventory Outstanding | 365 / Turnover | <90 days | Monthly |
| Stock-Out Incidents | Count(MD04 "unavailable") | <2 per month | Weekly |
| Obsolete Stock % | Aged Stock (>180 days) / Total | <5% | Monthly |
| Procurement Lead Time | Days from PO (EKKO) to GRN (MSEG) | <14 days | Monthly |

---

## 7. Scope & Constraints

### 7.1 In Scope

- Integration of FI (Company Code NV01), MM (Plants PL01, PL02), and SD (Sales Organization NV10) data.
- Three active reporting personas with dedicated dashboard suites.
- Order-to-Cash (O2C) and Revenue-to-Receivables (R2R) process tracking.
- Month-end close automation and GL reconciliation.
- Master data governance (Material Master MARA, Customer Master KNA1, GL Master T-Code FS00).

### 7.2 Out of Scope (Phase 2 Enhancements)

- Predictive analytics (demand forecasting, churn prediction) — requires historical data accumulation.
- AP-to-PO (Procure-to-Pay) module analytics — focused on purchasing processes beyond current scope.
- HR/Payroll analytics — out of module scope.
- Real-time ERP streaming — Phase 1 uses batch ETL with 4-hour freshness; real-time via OData/APIs in Phase 2.

### 7.3 Technical Constraints

- **Data Freshness:** 4–6 hour lag from transaction in SAP to analytics dashboard (batch ETL window).
- **Historical Data:** Initial go-live assumes 6 months of historical data for trend analysis.
- **Security:** Finance data (GL, customer AR) restricted to Finance Persona; Sales data restricted to Sales Persona; Inventory data to Supply Chain Persona.
- **Performance:** Dashboard queries must complete in <10 seconds (optimized through data warehouse indexing).

---

## 8. Roadmap & Phasing

### Phase 1 (Months 1–2): Foundation

- [ ] Design & build Star Schema data model (Fact: O2C_Facts, Dimension: Customer, Product, Plant, GL Account)
- [ ] Develop Python ETL (extract from SAP, transform, load to SQLite/PostgreSQL warehouse)
- [ ] Build Streamlit dashboards for three personas (basic revenue, inventory, GL dashboards)
- [ ] Implement GL reconciliation automation

### Phase 2 (Months 3–4): Enhancement

- [ ] Add predictive KPIs (forecast variance, churn risk scoring)
- [ ] Extend to Procure-to-Pay (P2P) analytics
- [ ] Implement real-time data sync via SAP OData API
- [ ] Add drill-down capability to source transaction (VBAK → MSEG → ACDOCA)

### Phase 3 (Months 5–6): Optimization

- [ ] Migrate to cloud data warehouse (AWS Redshift / Azure Synapse)
- [ ] Implement role-based security (RBAC) at data field level
- [ ] Build mobile dashboards for field sales team
- [ ] Establish data governance and SLA monitoring

---

## 9. Approval & Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Project Sponsor (CFO) | [Name] | [Date] | [Sign] |
| Technical Lead (Data Engineering) | [Name] | [Date] | [Sign] |
| Finance Controller (NV01) | [Name] | [Date] | [Sign] |
| Sales Director (NV10) | [Name] | [Date] | [Sign] |
| Supply Chain Manager | [Name] | [Date] | [Sign] |

---

**End of Analytics PRD Document**
