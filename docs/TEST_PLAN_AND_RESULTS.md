# Software Test Plan, Verification & Audit Results

**Document Standard:** Aligned with IEEE 829 Standard for Software Test Documentation  
**System:** ShadowLedger Value-Flow Reconstruction Engine  
**Version:** 1.0.0 (Production Final)  
**Test Execution Status:** 100% Passed (59 Unit Tests &bull; 2 Ground-Truth Benchmarks &bull; Remote CI Passed)  

---

## 1. Test Strategy & Scope

The ShadowLedger testing strategy is organized into a four-tier verification pyramid:

```
                            ▲
                           / \
                          /   \
                         /     \
                        /   E2E \      [10k Multi-Scenario Benchmarks & Hero Demos]
                       /─────────\
                      / Adversary \    [Adversarial Attacks & Decision Invariants]
                     /─────────────\
                    /  Concurrency  \  [Multi-Threaded DuckDB Lock & Query Safety]
                   /─────────────────\
                  /    Unit & Logic   \ [Normalization, Math Reconciler, Hypotheses]
                 /─────────────────────\
```

---

## 2. Test Suites & Coverage Breakdown

### 2.1 Unit & Logic Tests (38 Tests)
- **Data Normalization (`test_normalizer.py`, `test_ingest.py`):**
  - Canonical timestamp parsing across UTC/ISO/RFC formats.
  - High-precision Decimal amount cleaning and malformed row isolation.
  - Inventory movement normalization and schema validation.
- **Deterministic Reconciler (`test_reconciler.py`):**
  - Exact 1-to-1 match resolution (`POS == Bank`).
  - Standard fee-balanced matching (`POS - 2% MDR == Bank`).
  - Kirana non-monetary inventory change settlement (`POS - Candy == Bank`).
  - Dual payment leg deduplication (identical POS and Gateway amounts for single order).
- **Graph & Hypothesis Engine (`test_graph_builder.py`, `test_hypothesis_engine.py`):**
  - Node and edge construction with provenance labels.
  - Multi-hypothesis generation (`refund`, `fee_adjustment`, `store_credit`, `timing_offset`, `off_ledger_deviation`).
- **Evidence Scorer & Decision Gates (`test_evidence_scorer.py`, `test_decision_gate.py`):**
  - 7D mathematical confidence calibration.
  - Scale invariance (scoring depends on evidence, not monetary scale).
  - Materiality ceiling and off-ledger auto-resolve prohibition.
- **Pattern Engine & Persistence (`test_pattern_engine.py`, `test_database.py`, `test_shadow_ledger.py`):**
  - Cross-case signature clustering.
  - Roundtrip persistence of observations, inventory, cases, and batches in DuckDB.
  - Immutable audit trail provenance recording.

---

### 2.2 Adversarial & Security Test Suite (7 Tests)
Located in `apps/api/tests/test_adversarial_suite.py` and `test_adversarial.py`:

| Test ID | Test Scenario | Attack / Edge Vector | Expected Invariant | Result |
| :--- | :--- | :--- | :--- | :--- |
| **ADV-01** | Deceptive Near-Match | Amount discrepancy of ₹0.50 with conflicting entity IDs | Must NOT auto-resolve; flag contradiction penalty | ✅ PASS |
| **ADV-02** | Impossible Sequence | Bank deposit timestamp occurs before POS order creation | Penalize temporal score; escalate to human review | ✅ PASS |
| **ADV-03** | Invisible Cash Deviation | Off-ledger cash payment with zero digital trace | Strict safety refusal $\rightarrow$ `UNRESOLVED` | ✅ PASS |
| **ADV-04** | Extreme Timing Drift | Settlement offset exceeds 30-day business window | Decay temporal confidence $\rightarrow$ require human review | ✅ PASS |
| **ADV-05** | Competing Merchants | Conflicting merchant identifiers on identical order ID | Trigger contradiction penalty $\rightarrow$ reject hypothesis | ✅ PASS |
| **ADV-06** | Prompt Injection | Ingested notes contain malicious prompt override instructions | Sanitizer strips instruction; local AI remains robust | ✅ PASS |
| **ADV-07** | Offline AI Graceful Fallback | Local LLM server is unreachable or times out | Instant fallback to deterministic template synthesizer | ✅ PASS |

---

### 2.3 Concurrency & Thread-Safety Test Suite (8 Tests)
Located in `apps/api/tests/test_concurrency.py`:

| Test ID | Scenario | Concurrency Level | Invariant Enforced | Result |
| :--- | :--- | :--- | :--- | :--- |
| **CONC-01** | Concurrent Metrics Reads | 10 parallel threads querying `/api/metrics` | Zero cursor lock contention or 500 errors | ✅ PASS |
| **CONC-02** | Repeated Cases Requests | 15 parallel requests querying `/api/cases` | All threads receive HTTP 200 with valid JSON | ✅ PASS |
| **CONC-03** | Concurrent Pattern Requests | 10 parallel requests to `/api/patterns` | Consistent cluster counts across all threads | ✅ PASS |
| **CONC-04** | Simultaneous Benchmarks | 5 simultaneous benchmark runs | Thread-safe database writes and isolation | ✅ PASS |
| **CONC-05** | Metrics during Benchmark | Read metrics while 10k benchmark processes | Reader threads complete without blocking | ✅ PASS |
| **CONC-06** | Cases during Ingestion | Query cases while ingesting large batch | Non-blocking read operations | ✅ PASS |
| **CONC-07** | Multi-Threaded DB Writes | 20 threads writing observations simultaneously | Strict ACID transactions in DuckDB | ✅ PASS |
| **CONC-08** | Sequential Baseline Check | Sequential baseline execution consistency | Exact metric reproducibility | ✅ PASS |

---

## 3. Ground-Truth 10,000-Record Benchmark Execution Results

### 3.1 Primary Evaluation (Seed 42)

```
        Scenario-by-Scenario Evaluation Breakdown (Ground-Truth Audited)        
┏━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━┳━━━━━━━┳━━━━━━━┳━━━━━━━┳━━━━━━━┳━━━━━━━┳━━━━━━━━┓
┃             ┃       ┃ Stage ┃ Stage ┃ Stage ┃       ┃       ┃       ┃ Evalu… ┃
┃             ┃ Case  ┃ 1     ┃ 2     ┃ 2     ┃ Human ┃       ┃ Hypo… ┃ Outco… ┃
┃ Scenario ID ┃ Pop.  ┃ Exact ┃ Cases ┃ Auto  ┃ Revi… ┃ Unre… ┃ Alig… ┃ / Mode ┃
┡━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━╇━━━━━━━╇━━━━━━━╇━━━━━━━╇━━━━━━━╇━━━━━━━╇━━━━━━━━┩
│ SCN_01      │ 1,880 │ 1,880 │ 0     │ 0     │ 0     │ 0     │ N/A   │ Exact  │
│ SCN_02      │ 352   │ 0     │ 352   │ 0     │ 352   │ 0     │ 100%  │ Latent │
│ SCN_03      │ 375   │ 375   │ 0     │ 0     │ 0     │ 0     │ 100%  │ Latent │
│ SCN_04      │ 214   │ 214   │ 0     │ 0     │ 0     │ 0     │ 100%  │ Latent │
│ SCN_05      │ 180   │ 0     │ 180   │ 0     │ 180   │ 0     │ 100%  │ Latent │
│ SCN_06      │ 178   │ 178   │ 0     │ 0     │ 0     │ 0     │ 100%  │ Latent │
│ SCN_07      │ 197   │ 197   │ 0     │ 0     │ 0     │ 0     │ 100%  │ Latent │
│ SCN_08      │ 100   │ 0     │ 100   │ 0     │ 100   │ 0     │ 100%  │ Latent │
│ SCN_09      │ 72    │ 0     │ 72    │ 0     │ 0     │ 72    │ N/A   │ Unobs. │
│ SCN_10      │ 66    │ 0     │ 66    │ 0     │ 0     │ 66    │ N/A   │ Clust. │
│ SCN_11      │ 41    │ 0     │ 41    │ 0     │ 41    │ 0     │ N/A   │ Batch  │
│ SCN_12      │ 158   │ 0     │ 158   │ 0     │ 158   │ 0     │ N/A   │ Refuse │
└─────────────┴───────┴───────┴───────┴───────┴───────┴───────┴───────┴────────┘
```

### 3.2 Held-Out Generalization Evaluation (Seed 999)
- **Baseline Match Rate:** $81.57\%$ (8,157 / 10,000 records)
- **Synthetic Scenario Hypothesis Alignment:** **100.00% (1,596 / 1,596)**
- **Unsafe False Auto-Resolutions:** **0 (100% Policy Safe)**
- **Stage 2 Winning Latent Hypotheses:** 632 / 632 ($100.0\%$)
- **UNKNOWN Cases:** **0**

---

## 4. Continuous Integration (CI) Audit

Remote GitHub Actions Run `33497433095` on commit `3191303`:
- `backend`: ✅ PASSED (57s) — Ruff, Mypy, 59 Pytest tests
- `frontend`: ✅ PASSED (40s) — ESLint, TypeScript compiler, Next.js build
- `smoke`: ✅ PASSED (33s) — Benchmark validation & End-to-end integration
