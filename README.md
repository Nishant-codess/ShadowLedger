# ShadowLedger

<p align="center">
  <strong>Uncertainty-Aware Value-Flow Reconstruction Engine for Finance Operations</strong><br>
  <em>Built for the <strong>Razorpay AI Buildathon — Track 04: AI Finance Controller</strong></em><br>
  Zero-Paid-API Architecture &bull; Local-First &bull; Deterministic Truth Authority &bull; Graph-Inference Pipeline
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12%20%7C%203.13-blue?logo=python&logoColor=white" alt="Python Version" />
  <img src="https://img.shields.io/badge/Next.js-16.3-black?logo=next.js&logoColor=white" alt="Next.js" />
  <img src="https://img.shields.io/badge/DuckDB-1.4.5-yellow?logo=duckdb&logoColor=black" alt="DuckDB" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Tests-59%20Passed-brightgreen" alt="Tests" />
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License" />
</p>

---

## 📚 Complete Documentation Suite

Comprehensive engineering, academic, and operational specifications are available in the [`/docs`](./docs) directory:

| Document | Description | Target Audience |
| :--- | :--- | :--- |
| **[Product Requirements Document (PRD)](./docs/PRD.md)** | Product vision, user personas, epic breakdown, hero scenarios, and acceptance criteria | Product Managers, Stakeholders |
| **[System Architecture & APIs](./docs/SYSTEM_ARCHITECTURE.md)** | 7-stage pipeline, C4 model, local-first design, complete REST API specification & payloads | System Architects, Integrators |
| **[Database Schema & Storage](./docs/DATABASE_SCHEMA.md)** | Embedded DuckDB 1.4.5 architecture, ER diagrams, DDLs, and thread-safe lock mechanisms | Database Engineers, DevOps |
| **[Engineering Decisions & ADRs](./docs/ENGINEERING_DECISIONS.md)** | 7 Architecture Decision Records (ADRs) explaining core design tradeoffs | Lead Engineers, Code Reviewers |
| **[Academic Research Report](./docs/ACADEMIC_RESEARCH_REPORT.md)** | Literature review, theoretical graph formulation, conservation equations, and APA citations | Researchers, Academic Evaluators |
| **[Operator & User Manual](./docs/USER_MANUAL.md)** | Step-by-step navigation guide, graph visualizer walkthrough, and decision playbook | Financial Controllers, Analysts |
| **[Test Plan & Audit Results](./docs/TEST_PLAN_AND_RESULTS.md)** | IEEE 829 test specifications, 59 unit tests, adversarial attacks, and benchmark audit | QA Engineers, Security Auditors |

---

## 1. What Problem ShadowLedger Solves

Traditional financial reconciliation software matches records strictly on equality (`POS.amount == Bank.amount`). When records disagree by even $₹2$, legacy tools flag an "unmatched exception" and dump it into an unranked human queue.

In emerging-market commerce (e.g. Indian retail, mobility, and e-commerce), **discrepancies are rarely simple clerical errors**:
1. **Multi-Leg Non-Monetary Settlement**: A ₹98 retail bill settled with ₹100 cash and ₹2 chocolate candy as physical change.
2. **Off-Ledger Deviations**: A cab ride officially booked at ₹150 where the driver demands ₹200 with an unrecorded ₹50 cash or direct QR deviation.
3. **Implicit Intermediary Deductions**: Payment gateways deducting ~2.0% MDR fees before gross settlement.
4. **Timing Asynchrony**: Batches splitting across T+1 / T+2 settlement windows and bank holidays.

ShadowLedger reconciles **economic value flows**, not just static rows. It reconstructs what actually happened while strictly quantifying evidence confidence and enforcing auditable safety gates.

---

## 2. Why ShadowLedger Exists

In high-volume fintech and payment operations, operations teams are overwhelmed by thousands of daily micro-discrepancies. Existing solutions either:
- **Blindly Auto-Resolve (Dangerous)**: Fuzzy-matching transactions based on heuristic score thresholds, risking financial leakage and erroneous ledger adjustments.
- **Over-Escalate (Expensive)**: Forcing human operators to manually investigate tens of thousands of repetitive, structural discrepancies.

ShadowLedger provides an **uncertainty-aware financial reconstruction engine** that:
- Separates observed facts from derived facts, inferred latent events, and unobserved off-ledger deviations.
- Resolves safe, deterministic discrepancies automatically.
- Surfaces high-risk deviations with structured value-flow graphs, evidence breakdowns, and cross-case pattern discovery for human operators.
- Protects the immutable Official Ledger at all times.

---

## 3. Why Ordinary Reconciliation Fails

| Dimension | Legacy 2-Way / 3-Way Reconciliation | ShadowLedger Value-Flow Engine |
| :--- | :--- | :--- |
| **Model** | Row-to-row matching (`POS.amount == Bank.amount`) | Case-local directed value-flow graph (`Conservation of Value`) |
| **Non-Monetary Settlements** | Fails with ₹2 exception | Reconciles via linked inventory movement (`Chocolate Change`) |
| **Gateway Fees** | Fails or requires hardcoded manual rules | Infers derived fee events and proves conservation closure |
| **Off-Ledger Deviations** | Fails silently or leaves unresolvable orphan | Detects economic deviation, computes materiality, and enforces human review |
| **Risk Handling** | Binary (Matched vs Unmatched) | Calibrated 7-dimension evidence confidence &bull; 4 decision gates |
| **Cross-Case Fleet Noise** | 1,000 independent exception rows | Collapses 1,000 exceptions into 3 structural recurring patterns |

---

## 4. Core Innovations

### A. The Two Parallel Ledgers
- **Official Ledger (`observations` table)**: The immutable record of source observations ingested from POS terminals, bank statements, payment gateways, and mobility platforms.
- **Shadow Ledger (`cases`, `hypotheses`, `audit_events`)**: The candidate economic reconstruction constructed by the engine, detailing inferred latent events, inventory moves, and fee deductions without modifying source facts.

### B. 4-Level Event Taxonomy
```
Level 1: OBSERVED             Direct record from source systems (POS, Bank, Gateway)
    ↓
Level 2: DERIVED              Mathematically implied from observations (e.g. 2% MDR fee)
    ↓
Level 3: INFERRED_LATENT      Latent economic event supported by connected evidence
    ↓
Level 4: UNOBSERVED_DEVIATION Off-ledger economic gap (PROHIBITED FROM AUTO-RESOLVE)
```

### C. 7-Dimensional Calibrated Evidence Function
Every candidate hypothesis is scored across 7 mathematical dimensions:
1. **Mathematical Conservation**: $\Delta = \sum \text{Inflow} - \sum \text{Outflow} = 0$.
2. **Temporal Plausibility**: Sequence ordering and T+1 to T+3 business windows.
3. **Entity Linkage**: Shared order IDs, payment IDs, ride IDs, driver IDs.
4. **Direct Observation Coverage**: Ratio of explained source records.
5. **Domain Rule Fit**: Alignment with known fee schedules and retail price points.
6. **Parsimony Penalty**: Penalizing multi-step unverified assumptions.
7. **Contradiction Cost**: Strict disqualification on conflicting entity metadata.

---

## 5. System Architecture

```
[ Ingestion Layer: POS / Bank / Gateway / Platform / Inventory ]
                         │
                         ▼
             [ Normalizer & Deduplicator ]
                         │
                         ▼
        [ Stage 1: Deterministic Reconciler (Baseline) ]
             ├── Exact Matches ──► [ Matched Official Ledger ]
             └── Discrepancies ──► [ Case Clustering ]
                                         │
                                         ▼
            [ Stage 2-3: Value-Flow Graph Builder (NetworkX) ]
                                         │
                                         ▼
            [ Stage 4: Hypothesis Generation & Constraint Engine ]
                                         │
                                         ▼
            [ Stage 5: 7-Dimension Evidence Confidence Scorer ]
                                         │
                                         ▼
            [ Stage 6: Decision Risk Gate (Safety Invariants) ]
                                         │
                                         ▼
            [ Stage 7: Cross-Case Pattern Engine (Fleet Discovery) ]
                         │               │
                         ▼               ▼
              [ Embedded DuckDB 1.4.5 Storage ]
                         │
                         ▼
             [ FastAPI Backend Engine ] ──► [ Local AI Explainer (Ollama / Offline Fallback) ]
                         │
                         ▼
             [ Next.js 16 Web Command Center ]
```

---

## 6. Authoritative Benchmark Results (10,000 Records)

Evaluated on 10,000 multi-source transactions across 12 economic scenario families against independent hidden ground truth (Seed 42):

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Layer 1: Deterministic Baseline Correctness                                    ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Total Ingested Records           10,000 records                                │
│ Deterministic Exact-Match Rate   81.57% (8,157 records cleanly balanced)       │
│ Baseline Explained Volume        ₹49,312,472.31                                │
│ Unmatched Exception Records      1,843 records                                 │
├────────────────────────────────────────────────────────────────────────────────┤
┃ Layer 2: ShadowLedger Value-Flow Reconstruction & Attribution                  ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Structured Investigation Cases   1,843 raw records → 969 structured cases      │
│ Total Model-Attributed Volume    ₹50,770,611.31 (+₹1,458,139.00 attributed)    │
│ Unexplained Residual at Risk     ₹1,458,139.00 → ₹174,730.56 (88.0% drop)      │
│ Synthetic Scenario Alignment     100.00% (1,596 / 1,596 eligible contracts)    │
│ Stage 2 Latent Inference Match   632 / 632 correct selected hypotheses         │
├────────────────────────────────────────────────────────────────────────────────┤
┃ Layer 3: Safety & Decision Risk Gates                                          ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Unsafe Auto-Resolutions          0 (100% Policy Safe, zero fabricated guesses) │
│ Human Review Escalations         831 cases ranked with value-flow graphs       │
│ Explicitly Unresolved Cases      138 cases ("We don't know" safe refusal)      │
│ Engine Processing Throughput     78,778.4 records/sec (126.9ms total time)     │
└━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┘
```

---

## 7. Live Hero Scenarios (5-Minute Interactive Demo)

Launchable directly via 1-click on the Command Center (`/`):

### Hero A: Kirana Non-Monetary Chocolate Change (`hero_a_kirana`)
- **Official Ledger**: POS Sale ₹100.00 vs Bank Settlement ₹98.00 (₹2.00 shortfall).
- **Physical Reality**: Customer paid ₹100 cash; merchant returned ₹2 Dairy Milk chocolate candy change.
- **ShadowLedger Resolution**: Connects POS inventory movement to transaction graph, reconstructs Level 3 `INVENTORY_SETTLEMENT`, achieves mathematical conservation closure ($₹98 + ₹2 = ₹100$), and safely auto-resolves with $0.95$ confidence.

### Hero B: Mobility Off-Ledger Fare Deviation (`hero_b_mobility`)
- **Official Ledger**: Cab ride officially booked at ₹150.00.
- **Physical Reality**: True fare paid was ₹200.00 (₹50 unrecorded off-ledger cash/QR deviation).
- **Ride 1 (Digital QR Trace)**: External UPI trace found &rarr; Level 4 `OFF_LEDGER_DEVIATION` generated &rarr; **Enforces `HUMAN_REVIEW`** (Never auto-resolves).
- **Ride 2 (Cash Invisible)**: Zero digital trace found &rarr; **Explicitly marked `UNRESOLVED`** (*"We don't know"*).

### Hero C: Fleet Cross-Case Pattern Discovery (`hero_c_patterns`)
- **Fleet Scale**: 60 multi-party discrepancy records across 30 transactions.
- **Structural Collapse**: Reconstructs cases and automatically collapses the entire exception queue into **3 systemic operational patterns**:
  1. `FEE_ADJUSTMENT` (13 cases, ₹55,360 at risk): Payment gateway MDR fee deductions (2.0% standard rate).
  2. `OFF_LEDGER_DEVIATION` (10 cases, ₹2,000 at risk): Recurring mobility fare deviation pattern.
  3. `INVENTORY_SETTLEMENT` (7 cases, ₹1,190 at risk): Recurring non-cash inventory settlement pattern.

---

## 8. Quickstart & Local Setup

### Prerequisites
- Python 3.12+ (tested on Python 3.12, 3.13)
- Node.js 20.9+
- npm 10+

### Installation & Startup
```bash
# 1. Clone repository
git clone https://github.com/Nishant-codess/ShadowLedger.git
cd ShadowLedger

# 2. Set up Python environment & install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -e "./apps/api[dev]"

# 3. Install web frontend dependencies
cd apps/web && npm install && cd ../..

# 4. Run full test suite
pytest apps/api/tests -v

# 5. Start development servers
# Terminal 1: Backend API on :8000
PYTHONPATH=. uvicorn app.main:app --app-dir apps/api --reload --port 8000

# Terminal 2: Web Console on :3000
cd apps/web && npm run dev
```

Visit **`http://localhost:3000`** in your browser.

---

## 9. Running Benchmarks

```bash
# Run 10,000-record benchmark against ground truth
python scripts/run_benchmark.py --rows 10000 --seed 42

# Run on held-out evaluation dataset (unseen seed)
python scripts/run_benchmark.py --rows 10000 --seed 999
```

---

## 10. Local AI Explainer & Environment Configuration

ShadowLedger uses local LLMs strictly for **operator-facing audit narratives**. Arithmetic, reconciliation, scoring, and decision gates are 100% deterministic and cannot be overridden by AI.

### Configuration (`.env` or Environment Variables)
```bash
# Optional local Ollama integration (defaults to offline fallback if not running)
OLLAMA_BASE_URL="http://localhost:11434"
LLM_MODEL="llama3.2:latest" # or qwen3:8b
LLM_PROVIDER="ollama"
```

If Ollama is not installed or unreachable, the system automatically uses its built-in **Deterministic Synthesis Fallback**, providing instant, evidence-grounded policy briefings with zero external latency.

---

## 11. License & Hackathon Submission Notice

Developed for the **Razorpay AI Buildathon — Track 04 (AI Finance Controller)**.  
MIT License &bull; Free and Open Source.
