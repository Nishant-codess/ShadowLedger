# System Architecture & API Specification

**System Name:** ShadowLedger Value-Flow Reconstruction Engine  
**Version:** 1.0.0 (Production Final)  
**Architecture Paradigm:** Local-First &bull; Deterministic Authority &bull; Graph-Inference Pipeline &bull; Embedded DuckDB  

---

## 1. High-Level Architectural Overview

ShadowLedger operates on a layered, pipeline architecture designed for high throughput, auditable evidence generation, and absolute zero reliance on external paid cloud APIs.

```
                     ┌────────────────────────────────────────────────────────┐
                     │          INGESTION & NORMALIZATION LAYER               │
                     │  - Multi-source logs (POS, Gateway, Bank, Ride, Inv)   │
                     │  - Timestamp Canonicalization (UTC) & Exact Decimals   │
                     └───────────────────────────┬────────────────────────────┘
                                                 │
                                                 ▼
                     ┌────────────────────────────────────────────────────────┐
                     │     STAGE 1: HIGH-THROUGHPUT DETERMINISTIC RECONCILER  │
                     │  - Exact 1-to-1 Matches & Fee Balanced Pairs           │
                     │  - Non-Monetary Inventory Settlements (Kirana Candy)   │
                     │  - Multi-Source Dual Payment Deduplication             │
                     └───────────────────────────┬────────────────────────────┘
                                                 │
                                    ┌────────────┴────────────┐
                                    │                         │
                           [Deterministic Matches]   [Unmatched Exceptions]
                                    │                         │
                                    ▼                         ▼
                        ┌───────────────────────┐ ┌───────────────────────────────────┐
                        │   MATCHED RECONCILED  │ │  STAGE 2: VALUE-FLOW ENGINE       │
                        │   (Official Ledger)   │ │  - Case-Local Value Graph Builder │
                        │                       │ │  - Latent Hypothesis Generator    │
                        │                       │ │  - 7D Mathematical Evidence Scorer│
                        │                       │ │  - Hardened Decision Risk Gates   │
                        │                       │ │  - Fleet Cross-Case Pattern Engine│
                        │                       │ │  - Shadow Ledger Candidate Events │
                        └───────────────────────┘ └─────────────────┬─────────────────┘
                                                                    │
                                                                    ▼
                                                  ┌───────────────────────────────────┐
                                                  │       PERSISTENCE & APIS          │
                                                  │  - Embedded DuckDB 1.4.5 (ACID)   │
                                                  │  - FastAPI High-Concurrency Server│
                                                  │  - Next.js 16.3 Modern Workbench  │
                                                  └───────────────────────────────────┘
```

---

## 2. The 7-Stage Value-Flow Reconstruction Pipeline

### Stage 1: Ingestion & Normalization (`app.data.normalize`)
- Converts raw input dictionaries, JSON strings, or CSV files into canonical `ObservationRecord` and `InventoryMovement` models.
- Parses diverse timestamp formats (ISO-8601, RFC-2822, custom dates) into canonical UTC datetime strings.
- Enforces high-precision Python `Decimal` arithmetic to eliminate floating-point rounding errors.

### Stage 2: Deterministic Baseline Reconciliation (`app.engine.reconciler`)
- Groups records by `order_id` / `source_record_id`.
- Resolves exact 1-to-1 matches (`POS == Bank`).
- Balances standard fee deductions (`POS - Fee == Bank`).
- Resolves Kirana non-monetary physical change substitutions (`POS - Inventory == Bank`).
- Deduplicates multi-source capture legs where both POS and Gateway record identical amounts for the same order.
- Yields a **Stage 1 Baseline Match Rate** ($81.57\%$ on benchmark datasets).

### Stage 3: Case-Local Value Graph Construction (`app.engine.graph_builder`)
- For all unmatched records, constructs a directed value-flow graph $G = (V, E)$.
- **Nodes ($V$):** Entity accounts, external ledgers, inventory pools, and observed transaction events.
- **Edges ($E$):** Value transfers labeled with amount, currency, direction, and evidence provenance.

### Stage 4: Latent Hypothesis Generation (`app.engine.hypothesis_engine`)
- Synthesizes candidate economic explanations for unresolved balances:
  - `REFUND`: Customer return / partial refund cycle.
  - `FEE_ADJUSTMENT`: Unrecorded payment gateway MDR surcharge.
  - `INVENTORY_SETTLEMENT`: Physical commodity substitution.
  - `TIMING_OFFSET`: Delayed settlement window (T+1/T+2).
  - `STORE_CREDIT`: Customer wallet or credit carry-forward.
  - `OFF_LEDGER_DEVIATION`: Unobserved cash or direct driver UPI QR transaction.

### Stage 5: 7-Dimensional Evidence Scoring & Decision Risk Gate (`app.engine.evidence_scorer`, `app.engine.decision_gate`)
- Evaluates hypotheses against mathematical invariants:
  1. *Conservation of Value*: $\Delta = \sum \text{Inflow} - \sum \text{Outflow} = 0$.
  2. *Temporal Plausibility*: Plausible business sequencing and timing drift penalty.
  3. *Entity Linkage*: Shared merchant, customer, order, or trip IDs.
  4. *Observation Coverage*: Ratio of explained input records.
  5. *Domain Rule Fit*: Standard fee percentages ($1.5\% - 2.5\%$) and retail denominations.
  6. *Parsimony Penalty*: Occam's razor penalty on unverified multi-step paths.
  7. *Contradiction Penalty*: Strict disqualification on entity conflicts.
- **Decision Gates:**
  - `AUTO_RESOLVE`: Permitted only for Level 1/2/3 events with confidence $\ge 0.85$ and materiality $< ₹5,000$.
  - `HUMAN_REVIEW`: Mandatory for all Level 4 (`OFF_LEDGER_DEVIATION`) events, high materiality, or moderate confidence ($0.60 \le \text{conf} < 0.85$).
  - `UNRESOLVED`: Safe refusal when evidence is absent ($< 0.60$). Zero hallucination.

### Stage 6: Fleet Cross-Case Pattern Discovery (`app.engine.pattern_engine`)
- Scans all exception cases across the ingested batch.
- Clusters cases by signature (`REFUND`, `OFF_LEDGER_DEVIATION`, `FEE_ADJUSTMENT`, `INVENTORY_SETTLEMENT`).
- Computes aggregate value at risk, average variance, and produces structural operational insights.

### Stage 7: Shadow Ledger & Provenance Audit Trail (`app.engine.shadow_ledger`)
- Generates candidate `ShadowEvent` records representing the reconstructed economic state.
- Stores immutable audit logs documenting hypothesis selection, rule execution, and operator overrides.

---

## 3. Comprehensive REST API Specification

Base URL: `http://localhost:8000`

### 3.1 System Health
#### `GET /health`
- **Description:** Checks server availability and database connectivity.
- **Response `200 OK`:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "timestamp": "2026-09-02T03:00:00Z"
}
```

---

### 3.2 Batch Ingestion & Processing
#### `POST /api/batch/process`
- **Description:** Ingests and processes a multi-source transaction batch through the 7-stage reconstruction pipeline.
- **Request Body:**
```json
{
  "batch_id": "batch_retail_001",
  "records": [
    {
      "source_record_id": "pos_101",
      "source_system": "pos",
      "amount": 98.00,
      "currency": "INR",
      "timestamp": "2026-09-01T10:00:00Z",
      "order_id": "ORD-101",
      "customer_id": "CUST-01",
      "merchant_id": "MKT-01"
    },
    {
      "source_record_id": "bank_101",
      "source_system": "bank_feed",
      "amount": 100.00,
      "currency": "INR",
      "timestamp": "2026-09-01T10:00:05Z",
      "order_id": "ORD-101",
      "customer_id": "CUST-01",
      "merchant_id": "MKT-01"
    }
  ],
  "inventory_movements": [
    {
      "movement_id": "inv_101",
      "sku": "CHOC-DM-02",
      "quantity": 1,
      "unit_retail_value": 2.00,
      "direction": "outflow",
      "timestamp": "2026-09-01T10:00:00Z",
      "order_id": "ORD-101"
    }
  ]
}
```
- **Response `200 OK`:**
```json
{
  "batch_id": "batch_retail_001",
  "total_records": 2,
  "matched_count": 2,
  "exception_count": 0,
  "case_count": 0,
  "total_volume": 100.00,
  "explained_volume": 100.00,
  "unexplained_volume": 0.00,
  "processing_time_ms": 4.12
}
```

---

### 3.3 Cases & Investigations
#### `GET /api/cases`
- **Description:** Lists investigation cases with optional filtering by status, priority, and batch.
- **Query Parameters:**
  - `status` (*string*, optional): `open`, `resolved`, `escalated`, `unresolved`
  - `priority` (*string*, optional): `low`, `medium`, `high`, `critical`
  - `batch_id` (*string*, optional)
  - `limit` (*integer*, default: 50)
- **Response `200 OK`:**
```json
{
  "total_cases": 1,
  "cases": [
    {
      "case_id": "case_507805805fff",
      "batch_id": "hero_kirana_demo",
      "order_id": "ORD-KIRANA-001",
      "status": "resolved",
      "priority": "low",
      "unexplained_amount": 2.00,
      "confidence": 0.95,
      "decision": "auto_resolve",
      "selected_hypothesis": "inventory_settlement"
    }
  ]
}
```

#### `GET /api/cases/{case_id}`
- **Description:** Retrieves detailed case dossier including graph nodes/edges, evaluated hypotheses, evidence breakdown, and local AI synthesis.
- **Response `200 OK`:**
```json
{
  "case_id": "case_507805805fff",
  "batch_id": "hero_kirana_demo",
  "order_id": "ORD-KIRANA-001",
  "records": [...],
  "graph": {
    "nodes": [
      {"id": "entity:CUST-01", "type": "customer", "label": "Customer 01"},
      {"id": "entity:MKT-01", "type": "merchant", "label": "Kirana Store"},
      {"id": "event:pos_101", "type": "observation", "label": "POS Bill ₹98"}
    ],
    "edges": [
      {"source": "entity:CUST-01", "target": "entity:MKT-01", "amount": 100.00, "label": "Cash Tendered"}
    ]
  },
  "hypotheses": [
    {
      "hypothesis_id": "hyp_01",
      "hypothesis_type": "inventory_settlement",
      "confidence_score": 0.95,
      "confidence_tier": "DEFINITIVE",
      "dimension_scores": {
        "mathematical_conservation": 1.0,
        "temporal_plausibility": 1.0,
        "entity_linkage": 1.0,
        "observation_coverage": 1.0,
        "domain_rule_fit": 1.0,
        "parsimony": 0.95,
        "contradiction_penalty": 0.0
      }
    }
  ],
  "decision": {
    "decision": "auto_resolve",
    "reason_codes": ["AUTO_RESOLVED_INVENTORY_SETTLEMENT_HIGH_CONFIDENCE"]
  },
  "ai_explanation": "Reconciled ₹2 discrepancy via 1x Dairy Milk chocolate candy non-monetary physical change substitution."
}
```

#### `POST /api/cases/{case_id}/action`
- **Description:** Executes human operator action (Accept Hypothesis, Override Decision, Escalate, or Reject).
- **Request Body:**
```json
{
  "action": "accept",
  "hypothesis_id": "hyp_01",
  "operator_id": "analyst_arjun",
  "notes": "Verified chocolate inventory movement against Kirana daily register."
}
```
- **Response `200 OK`:**
```json
{
  "case_id": "case_507805805fff",
  "new_status": "resolved",
  "audit_event_id": "aud_984128",
  "updated_at": "2026-09-02T03:15:00Z"
}
```

---

### 3.4 Fleet Pattern Discovery
#### `GET /api/patterns`
- **Description:** Retrieves discovered systemic pattern clusters across cases.
- **Query Parameters:**
  - `batch_id` (*string*, optional)
- **Response `200 OK`:**
```json
{
  "total_clusters": 3,
  "clusters": [
    {
      "cluster_id": "pat_01",
      "pattern_signature": "FEE_ADJUSTMENT",
      "exception_count": 13,
      "total_value_at_risk": 55360.00,
      "likely_common_cause": "Systematic payment gateway MDR fee deduction across 13 settlements. Matches ~2.0% standard merchant discount rate."
    },
    {
      "cluster_id": "pat_02",
      "pattern_signature": "OFF_LEDGER_DEVIATION",
      "exception_count": 10,
      "total_value_at_risk": 2000.00,
      "likely_common_cause": "Recurring mobility fare deviation pattern across 10 trips. Possible off-ledger fare discrepancy."
    },
    {
      "cluster_id": "pat_03",
      "pattern_signature": "INVENTORY_SETTLEMENT",
      "exception_count": 7,
      "total_value_at_risk": 1190.00,
      "likely_common_cause": "Recurring non-cash inventory settlement pattern across 7 transactions. Possible physical change substitution pattern."
    }
  ]
}
```

---

### 3.5 Dynamic Benchmark Metrics
#### `GET /api/metrics/benchmark`
- **Description:** Returns ground-truth evaluated benchmark performance comparing Stage 1 baseline against the full ShadowLedger engine across all 12 economic scenario families.
- **Response `200 OK`:**
```json
{
  "batch_id": "benchmark_s42_r10000",
  "records": 10000,
  "baseline": {
    "matched_count": 8157,
    "exception_count": 1843,
    "match_rate": 81.57,
    "explained_volume": 49312472.31,
    "unexplained_volume": 1458139.00
  },
  "enhanced": {
    "cases_count": 969,
    "auto_resolved_count": 0,
    "human_review_count": 831,
    "unresolved_count": 138,
    "latent_hypothesis_accuracy": 100.0,
    "explained_volume": 50770611.31,
    "unexplained_volume": 174730.56,
    "scenario_breakdown": {
      "SCN_01": {"total": 1880, "exact_matches": 1880, "structured_cases": 0, "auto_resolved": 0, "human_review": 0, "unresolved": 0, "hypotheses_evaluated": 0, "correct_hypotheses": 0, "evaluation_mode": "clean_match"},
      "SCN_08": {"total": 100, "exact_matches": 0, "structured_cases": 100, "auto_resolved": 0, "human_review": 100, "unresolved": 0, "hypotheses_evaluated": 100, "correct_hypotheses": 100, "evaluation_mode": "latent_event"},
      "SCN_09": {"total": 72, "exact_matches": 0, "structured_cases": 72, "auto_resolved": 0, "human_review": 0, "unresolved": 72, "hypotheses_evaluated": 0, "correct_hypotheses": 0, "evaluation_mode": "unobserved_deviation"},
      "SCN_10": {"total": 66, "exact_matches": 0, "structured_cases": 66, "auto_resolved": 0, "human_review": 0, "unresolved": 66, "hypotheses_evaluated": 0, "correct_hypotheses": 0, "evaluation_mode": "pattern_clustering"}
    }
  }
}
```

---

### 3.6 Curated Hero Demonstrations
#### `POST /api/demo/hero/{hero_id}`
- **Parameters:**
  - `hero_id`: `hero_a`, `hero_b`, `hero_c`
- **Description:** Seeds and executes one of the three curated hero scenarios and returns live engine results for instant interactive evaluation.
