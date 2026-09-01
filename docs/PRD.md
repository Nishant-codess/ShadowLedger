# Product Requirements Document (PRD)

**Product Name:** ShadowLedger  
**Track:** Razorpay AI Buildathon — Track 04: AI Finance Controller  
**Version:** 1.0.0 (Production Final)  
**Status:** Approved & Frozen  
**Target Audience:** Fintech Operations Teams, Financial Controllers, Internal Audit Teams, Platform Merchants  

---

## 1. Executive Summary & Vision

Modern commerce in emerging markets (particularly India) is characterized by multi-party, asynchronous, and non-monetary transaction flows:
- **Kirana retail** substitutes physical chocolate candy or matchboxes for small change ($₹1$–$₹5$).
- **Mobility and ride-hailing** encounter off-ledger driver cash or direct UPI QR deviations ($₹20$–$₹100$).
- **E-commerce gateways** deduct dynamic merchant discount rate (MDR) fees ($1.5\%$–$2.5\%$) prior to net bank settlement.
- **Batches split** across T+1/T+2 settlement cutoffs and bank holidays.

Traditional 2-way and 3-way reconciliation software matches records strictly on equality (`POS.amount == Bank.amount`). When records diverge by even $₹2$, legacy systems flag an unranked exception and dump it into a massive human backlog.

**ShadowLedger** is an uncertainty-aware **Value-Flow Reconstruction Engine**. It reconstructs the underlying economic reality behind discrepancies, represents them as directed value-flow graphs, generates candidate economic hypotheses, calibrates evidence confidence across 7 mathematical dimensions, and enforces strict, auditable decision risk gates.

---

## 2. Product Goals & Non-Goals

### 2.1 Strategic Goals
1. **Explainable Attribution over Blind Matching:** Provide clear, auditable economic explanations for financial discrepancies instead of binary "matched/unmatched" flags.
2. **Deterministic Baseline Foundation:** Execute high-throughput deterministic matching on straightforward records before invoking graph inference.
3. **Strict Decision Safety Invariants:** Enforce that unverified or off-ledger events **never auto-resolve** into the Official Ledger without human oversight.
4. **Fleet-Level Pattern Discovery:** Aggregate thousands of recurring micro-deviations into actionable structural root causes (e.g. systematic gateway fee misconfigurations, recurring driver deviations).
5. **Zero-Paid-API & Local-First:** Complete all ingestion, normalization, graph inference, and AI explanation offline without cloud dependencies or paid APIs.

### 2.2 Explicit Non-Goals
- **No Direct Fund Movement / Disbursement:** ShadowLedger is an intelligence and audit controller; it does not directly debit or credit external bank accounts.
- **No Official Ledger Mutation:** Source observations from external systems are strictly immutable.
- **No Hallucinated Settlements:** When evidence is missing or ambiguous (e.g. unrecorded cash transactions), the system must state *"We don't know"* (`UNRESOLVED`) rather than guessing.
- **No "Recovered Money" Marketing Claims:** ShadowLedger attributes previously unexplained value; it does not collect funds.

---

## 3. User Personas & Target Users

| Persona | Role | Key Pain Points | ShadowLedger Value Proposition |
| :--- | :--- | :--- | :--- |
| **Priya Sharma** | Financial Controller | Unexplained residual balances at month-end; risk of unauthorized write-offs | Complete visibility into attributed value, calibrated risk gates, auditable audit trail. |
| **Arjun Mehta** | Reconciliation Ops Lead | Daily flood of 5,000+ unranked exception rows; manual ticket routing | Automated high-confidence resolutions, ranked human-review queues with pre-built evidence graphs. |
| **Rohan Das** | Fraud & Risk Auditor | Undetected systemic micro-leakages across merchant fleets | Cross-case Pattern Discovery Engine collapses micro-anomalies into systemic operational clusters. |

---

## 4. User Stories & Core Workflows

### Epic 1: High-Throughput Baseline Ingestion & Normalization
- **US-101:** As an Ops Analyst, I want to ingest multi-source batch logs (POS, Gateway, Bank, Ride Platform, Inventory) in JSON or CSV format so that records are normalized into canonical UTC timestamps and Decimal precision.
- **US-102:** As a System Auditor, I want duplicate transaction broadcasts (e.g., gateway retry webhooks) automatically identified and deduplicated in Stage 1.

### Epic 2: Value-Flow Graph Reconstruction & Latent Hypotheses
- **US-201:** As a Reconciler, when an order has an amount discrepancy, I want the engine to build a case-local value-flow graph connecting all related entities, orders, payments, and movements.
- **US-202:** As an Operator, I want the engine to evaluate candidate economic hypotheses (`refund`, `fee_adjustment`, `inventory_settlement`, `timing_offset`, `store_credit`, `off_ledger_deviation`) against conservation of value laws.

### Epic 3: Evidence Confidence & Decision Risk Gates
- **US-301:** As a Controller, I want every hypothesis scored on 7 calibrated dimensions (conservation, temporal plausibility, entity linkage, observation coverage, domain fit, parsimony, contradiction penalty).
- **US-302:** As a Risk Manager, I want high-risk or off-ledger events automatically escalated to `HUMAN_REVIEW` or marked `UNRESOLVED`, preventing fraudulent automated ledger balance closures.

### Epic 4: Fleet Cross-Case Pattern Discovery
- **US-401:** As an Auditor, I want the engine to group similar exception cases into structural pattern clusters so I can resolve thousands of recurring micro-leakages with a single root-cause action.

### Epic 5: Interactive Human Investigation Workbench
- **US-501:** As an Operator, I want an interactive web UI where I can inspect value-flow graphs, review evidence tiers, read local AI explanations, and accept or reject candidate resolutions.

---

## 5. Hero Scenarios & Demonstration Contracts

### Hero A: Kirana Non-Monetary Settlement (`hero_a_kirana`)
- **Context:** A customer purchases $₹98$ worth of groceries at a Kirana store, pays $₹100$ cash/UPI, and receives a $₹2$ Dairy Milk chocolate candy as physical change.
- **Input:** POS Bill ($₹98$), Bank Deposit ($₹100$), Inventory Move (1x Dairy Milk, retail value $₹2$).
- **Expected Outcome:** Reconciles deterministically via conservation of value: $₹98 \text{ (Goods)} + ₹2 \text{ (Candy)} = ₹100 \text{ (Tendered)}$. Confidence: $0.95$ (`DEFINITIVE`), Decision: `AUTO_RESOLVE`.

### Hero B: Mobility Fare Deviation & Safety Refusal (`hero_b_mobility`)
- **Context:** Two ride-hailing trips are booked at $₹150$ official platform fare. Both drivers demand $₹200$.
  - **Trip 1 (Digital Trace):** Passenger transfers $₹50$ extra via direct driver UPI QR.
  - **Trip 2 (Cash Only):** Passenger hands $₹50$ physical cash; zero digital trace exists.
- **Expected Outcome:**
  - Trip 1: Reconstructs off-ledger deviation using UPI trace graph $\rightarrow$ Confidence: $0.85$ (`HIGH`), Decision: **`HUMAN_REVIEW`** (Enforces safety invariant: Off-ledger events *never* auto-resolve).
  - Trip 2: No digital footprint $\rightarrow$ Confidence: $0.00$, Decision: **`UNRESOLVED`** (Strict safety refusal: Zero hallucination).

### Hero C: Fleet Cross-Case Pattern Discovery (`hero_c_patterns`)
- **Context:** 30 multi-party discrepancy cases across 60 raw logs.
- **Expected Outcome:** Pattern Discovery Engine collapses 30 individual cases into **3 distinct structural clusters**:
  1. *FEE_ADJUSTMENT* (13 cases, $₹55,360$ at risk) $\rightarrow$ Systematic 2.0% gateway MDR deduction.
  2. *OFF_LEDGER_DEVIATION* (10 cases, $₹2,000$ at risk) $\rightarrow$ Recurring mobility fare deviation pattern.
  3. *INVENTORY_SETTLEMENT* (7 cases, $₹1,190$ at risk) $\rightarrow$ Recurring non-cash inventory settlement pattern.

---

## 6. Functional & Non-Functional Requirements

### 6.1 Functional Requirements
- **FR-1:** Multi-format ingestion supporting JSON, CSV, and programmatic dictionaries.
- **FR-2:** Multi-source payment deduplication recognizing dual POS/Gateway capture legs for identical payment amounts.
- **FR-3:** 7-stage value-flow reconstruction pipeline executing in $<200\text{ms}$ for 10,000 records.
- **FR-4:** 4-level event taxonomy (`OBSERVED`, `DERIVED`, `INFERRED_LATENT`, `UNOBSERVED_DEVIATION`).
- **FR-5:** Offline Local AI synthesis module with rule-based deterministic fallback.
- **FR-6:** DuckDB embedded persistence supporting ACID transactions and thread-safe read/write concurrency locks.

### 6.2 Non-Functional Requirements
- **NFR-1 (Throughput):** Baseline matching $\ge 300,000\text{ records/sec}$; full Stage 2 graph reconstruction $\ge 50,000\text{ records/sec}$.
- **NFR-2 (Safety Invariant):** 0 unsafe auto-resolutions ($100\%$ policy safety on ground-truth adversarial benchmarks).
- **NFR-3 (Cost):** Zero cloud API costs (runs $100\%$ locally with embedded DuckDB 1.4.5 and local fallback).
- **NFR-4 (Portability):** Runs seamlessly on macOS, Linux, and Windows in modern Python 3.11+ environments.
