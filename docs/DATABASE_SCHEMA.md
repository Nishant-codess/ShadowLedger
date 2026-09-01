<div align="center">

# 🗄️ Database Schema & Storage Architecture

### **ShadowLedger Embedded Columnar Storage Model**

[![Database](https://img.shields.io/badge/Engine-DuckDB%201.4.5%20(Embedded)-F59E0B?style=for-the-badge&logo=duckdb)](file:///Users/nishant/Desktop/ShadowLedger/docs/DATABASE_SCHEMA.md)
[![Concurrency](https://img.shields.io/badge/Concurrency-RLock%20Synchronized%20Queries-10B981?style=for-the-badge)](file:///Users/nishant/Desktop/ShadowLedger/docs/DATABASE_SCHEMA.md)
[![Storage Type](https://img.shields.io/badge/Storage-Columnar%20File--Backed-6366F1?style=for-the-badge)](file:///Users/nishant/Desktop/ShadowLedger/docs/DATABASE_SCHEMA.md)

</div>

---

## 1. Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    BATCHES ||--o{ OBSERVATIONS : "contains (1:N)"
    BATCHES ||--o{ INVENTORY_MOVEMENTS : "contains (1:N)"
    BATCHES ||--o{ CASES : "generates (1:N)"
    BATCHES ||--o{ PATTERN_CLUSTERS : "discovers (1:N)"
    CASES ||--o{ AUDIT_EVENTS : "tracks (1:N)"

    BATCHES {
        string batch_id PK "Unique Batch Identifier"
        timestamp created_at "Batch Creation Timestamp"
        integer total_records "Total Raw Ingested Count"
        integer matched_count "Stage 1 Exact Matches"
        integer exception_count "Unmatched Exceptions"
        decimal total_volume "Gross Inflow (INR)"
        decimal explained_volume "Model-Attributed Value (INR)"
        decimal unexplained_volume "Residual Discrepancy (INR)"
        string status "Processing Lifecycle State"
    }

    OBSERVATIONS {
        string source_record_id PK "Immutable Record Identifier"
        string batch_id FK "Parent Batch Reference"
        string source_system "POS, Gateway, Bank, Ride"
        decimal amount "Exact Numerical Amount"
        string currency "ISO-4217 Currency (INR)"
        timestamp timestamp "Canonical UTC Timestamp"
        string order_id "Commercial Order ID"
        string customer_id "Customer Identifier"
        string merchant_id "Merchant Identifier"
        string payment_method "UPI, CARD, CASH, WALLET"
        string status "pending, matched, exception"
        json raw_metadata "Original Source Attributes"
    }

    INVENTORY_MOVEMENTS {
        string movement_id PK "Physical Stock Movement ID"
        string batch_id FK "Parent Batch Reference"
        string sku "Stock Keeping Unit (e.g. CHOC-DM-02)"
        string item_name "Product Description"
        integer quantity "Units Transferred"
        decimal unit_cost "Wholesale Cost Basis"
        decimal unit_retail_value "Retail Sales Denomination"
        string direction "inflow, outflow"
        timestamp timestamp "Movement Timestamp"
        string order_id "Linked Order Reference"
    }

    CASES {
        string case_id PK "Investigation Dossier ID"
        string batch_id FK "Parent Batch Reference"
        string order_id "Associated Order ID"
        string status "open, resolved, escalated, unresolved"
        string priority "low, medium, high, critical"
        decimal unexplained_amount "Discrepancy Magnitude"
        decimal confidence "Calibrated Evidence Score [0, 1]"
        string confidence_tier "DEFINITIVE, HIGH, MEDIUM, SPECULATIVE"
        string decision "auto_resolve, human_review, unresolved"
        string selected_hypothesis "refund, fee_adjustment, etc."
        json hypotheses_payload "Full Candidate Hypotheses Array"
        json graph_payload "Directed Graph Nodes & Edges"
        json reason_codes "Deterministic Policy Justifications"
        string ai_explanation "Local AI Narrative Summary"
        timestamp created_at "Case Inception Timestamp"
        timestamp updated_at "Last State Modification"
    }

    PATTERN_CLUSTERS {
        string cluster_id PK "Structural Cluster ID"
        string batch_id FK "Parent Batch Reference"
        string pattern_signature "FEE_ADJUSTMENT, OFF_LEDGER, etc."
        integer exception_count "Total Aggregated Cases"
        decimal total_value_at_risk "Cumulative Value Variance"
        decimal avg_discrepancy "Mean Exception Size"
        decimal confidence "Cluster Confidence Score"
        string likely_common_cause "Root Cause Operational Insight"
        json affected_case_ids "List of Linked Case UUIDs"
        timestamp discovered_at "Discovery Timestamp"
    }

    AUDIT_EVENTS {
        string event_id PK "Audit Log Identifier"
        string case_id FK "Subject Case Reference"
        string action "accept, override, escalate, reject"
        string previous_state "Prior Case Status"
        string new_state "Updated Case Status"
        string operator_id "Human Analyst Identifier"
        string notes "Audit Justification Notes"
        timestamp timestamp "Tamper-Evident Event Time"
    }
```

---

## 2. Multi-Threaded Query Isolation & Concurrency Safety

```mermaid
sequenceDiagram
    autonumber
    participant ThreadA as Worker Thread A (Batch Ingestion)
    participant ThreadB as Worker Thread B (Case Review API)
    participant DB as DatabaseManager (Singleton)
    participant Lock as threading.RLock()
    participant DuckDB as DuckDB Storage Engine

    Note over DB: High-Concurrency Lock Isolation
    ThreadA->>DB: execute_insert(batch_id, records)
    DB->>Lock: acquire()
    Lock-->>DB: Lock Granted
    DB->>DuckDB: Open Dedicated Cursor & Execute Insert
    DuckDB-->>DB: Commit Completed
    DB->>Lock: release()

    par Parallel Query Execution
        ThreadB->>DB: get_case_by_id(case_id)
        DB->>Lock: acquire()
        Lock-->>DB: Lock Granted
        DB->>DuckDB: Open Dedicated Cursor & Fetch Case JSON
        DuckDB-->>DB: Row Returned
        DB->>Lock: release()
        DB-->>ThreadB: Return Case Dossier
    end
```

---

## 3. Detailed Table Specifications & SQL DDLs

### 3.1 Table: `batches`
```sql
CREATE TABLE IF NOT EXISTS batches (
    batch_id VARCHAR PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    total_records INTEGER NOT NULL,
    matched_count INTEGER NOT NULL,
    exception_count INTEGER NOT NULL,
    total_volume DECIMAL(18, 4) NOT NULL,
    explained_volume DECIMAL(18, 4) NOT NULL,
    unexplained_volume DECIMAL(18, 4) NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'completed'
);
```

### 3.2 Table: `observations` (Official Ledger)
```sql
CREATE TABLE IF NOT EXISTS observations (
    source_record_id VARCHAR PRIMARY KEY,
    batch_id VARCHAR NOT NULL REFERENCES batches(batch_id),
    source_system VARCHAR NOT NULL,
    amount DECIMAL(18, 4) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'INR',
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    order_id VARCHAR,
    customer_id VARCHAR,
    merchant_id VARCHAR,
    payment_method VARCHAR,
    status VARCHAR NOT NULL DEFAULT 'pending',
    raw_metadata JSON
);

CREATE INDEX IF NOT EXISTS idx_obs_batch_order ON observations(batch_id, order_id);
CREATE INDEX IF NOT EXISTS idx_obs_timestamp ON observations(timestamp);
```

### 3.3 Table: `inventory_movements`
```sql
CREATE TABLE IF NOT EXISTS inventory_movements (
    movement_id VARCHAR PRIMARY KEY,
    batch_id VARCHAR NOT NULL REFERENCES batches(batch_id),
    sku VARCHAR NOT NULL,
    item_name VARCHAR NOT NULL,
    quantity INTEGER NOT NULL,
    unit_cost DECIMAL(18, 4) NOT NULL,
    unit_retail_value DECIMAL(18, 4) NOT NULL,
    direction VARCHAR NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    order_id VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_inv_order ON inventory_movements(order_id);
```

### 3.4 Table: `cases` (Investigation Dossiers)
```sql
CREATE TABLE IF NOT EXISTS cases (
    case_id VARCHAR PRIMARY KEY,
    batch_id VARCHAR NOT NULL REFERENCES batches(batch_id),
    order_id VARCHAR,
    status VARCHAR NOT NULL DEFAULT 'open',
    priority VARCHAR NOT NULL DEFAULT 'medium',
    unexplained_amount DECIMAL(18, 4) NOT NULL,
    confidence DECIMAL(5, 4) NOT NULL,
    confidence_tier VARCHAR NOT NULL,
    decision VARCHAR NOT NULL,
    selected_hypothesis VARCHAR,
    hypotheses_payload JSON,
    graph_payload JSON,
    reason_codes JSON,
    ai_explanation TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cases_batch_status ON cases(batch_id, status);
CREATE INDEX IF NOT EXISTS idx_cases_priority ON cases(priority);
```

### 3.5 Table: `pattern_clusters`
```sql
CREATE TABLE IF NOT EXISTS pattern_clusters (
    cluster_id VARCHAR PRIMARY KEY,
    batch_id VARCHAR NOT NULL REFERENCES batches(batch_id),
    pattern_signature VARCHAR NOT NULL,
    exception_count INTEGER NOT NULL,
    total_value_at_risk DECIMAL(18, 4) NOT NULL,
    avg_discrepancy DECIMAL(18, 4) NOT NULL,
    confidence DECIMAL(5, 4) NOT NULL,
    likely_common_cause TEXT,
    affected_case_ids JSON,
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_patterns_batch ON pattern_clusters(batch_id);
```

### 3.6 Table: `audit_events`
```sql
CREATE TABLE IF NOT EXISTS audit_events (
    event_id VARCHAR PRIMARY KEY,
    case_id VARCHAR NOT NULL REFERENCES cases(case_id),
    action VARCHAR NOT NULL,
    previous_state VARCHAR,
    new_state VARCHAR NOT NULL,
    operator_id VARCHAR NOT NULL,
    notes TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_case ON audit_events(case_id);
```
