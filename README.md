# ShadowLedger

> **Uncertainty-Aware Value-Flow Reconstruction Engine for Finance Operations**  
> Built for the **Razorpay AI Buildathon — Track 04: AI Finance Controller**  
> Zero-Paid-API Architecture &bull; Local-First &bull; Deterministic Truth Path &bull; Pure Rules Baseline

---

## 1. What Problem ShadowLedger Solves

Traditional financial reconciliation systems operate on a rigid paradigm: they compare two or more flat ledger files looking for exact key/amount matches. When records disagree (e.g. a ₹2 discrepancy, a missing bank settlement, or a split batch), legacy tools simply flag an "unmatched exception" and dump it into an unranked human queue.

In modern Indian and emerging-market commerce, **discrepancies are rarely simple clerical errors**:
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

ShadowLedger exists to provide an **uncertainty-aware financial reconstruction engine** that:
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
- **Official Ledger**: The immutable record of source observations ingested from POS terminals, bank statements, payment gateways, and mobility platforms.
- **Shadow Ledger**: The candidate economic reconstruction constructed by the engine, detailing inferred latent events, inventory moves, and fee deductions without modifying source facts.

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

### C. 4 Evidence Confidence Tiers
Every candidate hypothesis is scored across 7 mathematical dimensions:
1. **Mathematical Conservation**: $Residual = \sum Payments - (\sum Settlements + NonCash)$
2. **Temporal Plausibility**: Sequence ordering and T+1 to T+3 business windows.
3. **Entity Linkage**: Shared order IDs, payment IDs, ride IDs, driver IDs.
4. **Direct Observation Coverage**: Ratio of explained source records.
5. **Domain Rule Fit**: Alignment with known fee schedules and retail price points.
6. **Parsimony Penalty**: Penalizing multi-step unverified assumptions.
7. **Contradiction Cost**: Strict disqualification on conflicting entity metadata.

Resulting Confidence Tiers:
- `DEFINITIVE` ($\ge 0.95$): High-certainty, mathematically closed.
- `HIGH` ($\ge 0.80$): Strong multi-point evidence.
- `MEDIUM` ($\ge 0.60$): Plausible hypothesis; requires operator oversight.
- `SPECULATIVE` ($< 0.60$): Insufficient evidence &rarr; `UNRESOLVED`.

### D. Hardened Decision Risk Gates
- `AUTO_RESOLVE`: Only permitted for Level 1/2/3 events with high confidence and materiality below supervisor threshold (default: ₹5,000).
- `HUMAN_REVIEW`: Mandatory for all `OFF_LEDGER_DEVIATION` events and high-materiality cases.
- `ESCALATE`: High financial impact or contradictory evidence.
- `UNRESOLVED`: Incomplete information; explicit refusal to invent ungrounded explanations (*"We don't know"*).

---

## 5. Architecture

```
[ Ingestion Layer: POS / Bank / Gateway / Platform / Inventory ]
                         │
                         ▼
             [ Normalizer & Deduplicator ]
                         │
                         ▼
        [ Stage 1: Deterministic Reconciler (Baseline) ]
             ├── Exact Matches ──► [ Matched Ledger ]
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
            [ Stage 7: Cross-Case Pattern Engine (Fleet Collapse) ]
                         │               │
                         ▼               ▼
              [ Embedded DuckDB 1.4.5 Storage ]
                         │
                         ▼
             [ FastAPI Backend Engine ] ──► [ Local AI Explainer (Ollama / Offline) ]
                         │
                         ▼
             [ Next.js 16 Web Command Center ]
```

---

## 6. Technology Stack

- **Core Engine & Backend**: Python 3.12+, FastAPI, Pydantic v2.
- **Graph Modeling**: NetworkX (Case-local directed acyclic multigraphs).
- **Embedded Database**: DuckDB 1.4.5 (Zero-cloud dependency, local file storage).
- **Web Frontend**: Next.js 16 (App Router), TypeScript, Tailwind CSS, Lucide Icons.
- **Local AI Explainer**: Local Ollama (`llama3.2:latest`, `qwen3:8b`) with 100% deterministic offline fallback.
- **Testing & Quality**: Pytest, Ruff, Mypy, ESLint.

---

## 7. Quickstart & Local Setup

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

# 4. Run test suite
pytest apps/api/tests -v

# 5. Start development servers
# Terminal 1 (Backend API on :8000)
uvicorn app.main:app --app-dir apps/api --reload --port 8000

# Terminal 2 (Web Console on :3000)
cd apps/web && npm run dev
```

Visit **`http://localhost:3000`** in your browser.

---

## 8. Dataset Generation & Benchmarking

### Generate Synthetic Batches
```bash
# Generate 10,000 synthetic records with hidden ground truth
python scripts/generate_dataset.py --rows 10000 --seed 42
```

### Run Formal Benchmark (Side-by-Side Evaluation)
```bash
# Run 10,000-record benchmark against hidden ground truth
python scripts/run_benchmark.py --rows 10000 --seed 42

# Run on held-out evaluation dataset (unseen seed)
python scripts/run_benchmark.py --rows 10000 --seed 999
```

---

## 9. Authoritative Benchmark Results (10,000 Records)

Evaluated on 10,000 multi-source transactions across 12 scenario families against independent hidden ground truth:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Layer 1: Deterministic Baseline Correctness                                    ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Total Ingested Records           10,000                                        │
│ Deterministic Exact-Match Rate   25.17% (2,517 records cleanly balanced)      │
│ Deterministic Baseline Precision 100.00% (Zero false matches on exact path)    │
├────────────────────────────────────────────────────────────────────────────────┤
┃ Layer 2: ShadowLedger Value-Flow Reconstruction & Attribution                  ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Raw Unmatched Exceptions         7,483 raw records → 2,949 structured cases    │
│ Value Explained by Model         ₹35.45M baseline → ₹50.77M (+₹15.32M attributed)│
│ Unexplained Residual at Risk     ₹15.32M legacy residual → ₹174.7K (98.9% drop)│
│ Latent Hypothesis Ground Truth   100.00% fit across 12 scenario families       │
├────────────────────────────────────────────────────────────────────────────────┤
┃ Layer 3: Safety & Decision Risk Gates                                          ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Unsafe Auto-Resolutions          0 (100% Policy Safe, zero fabricated guesses) │
│ Human Review Escalations         2,949 cases ranked with value-flow graphs     │
│ Explicitly Unresolved Cases      Correctly returned "We don't know"            │
│ Engine Processing Throughput     27,100.6 records/sec (<370ms total time)      │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Live Hero Scenarios (5-Minute Demo Path)

Launchable directly via 1-click on the Command Center (`/`):

### Hero A: Kirana Non-Monetary Chocolate Change (`SCN_04`)
- **Official Ledger**: POS Sale ₹100.00 vs Bank Settlement ₹98.00 (₹2.00 shortfall).
- **Physical Reality**: Customer paid ₹100 cash; merchant returned ₹2 Dairy Milk chocolate change.
- **ShadowLedger Resolution**: Connects POS inventory decrement to transaction graph, reconstructs Level 3 `INVENTORY_SETTLEMENT`, achieves mathematical conservation closure ($₹98 + ₹2 = ₹100$), and safely resolves.

### Hero B: Mobility Off-Ledger Fare Deviation (`SCN_08` & `SCN_09`)
- **Official Ledger**: Cab ride officially booked at ₹150.00.
- **Physical Reality**: True fare paid was ₹200.00 (₹50 unrecorded off-ledger cash/QR deviation).
- **Ride 1 (Digital QR Trace)**: External UPI trace found &rarr; Level 4 `OFF_LEDGER_DEVIATION` generated &rarr; **Enforces `HUMAN_REVIEW`** (Never auto-resolves).
- **Ride 2 (Cash Invisible)**: Zero digital trace found &rarr; **Explicitly marked `UNRESOLVED`** (*"We don't know"*).

### Hero C: Fleet Cross-Case Pattern Discovery (P0)
- **Fleet Scale**: 60 multi-party discrepancy records across 30 transactions.
- **Structural Collapse**: Reconstructs cases and automatically collapses the entire exception queue into **3 systemic operational patterns**:
  1. `FEE_ADJUSTMENT`: Payment gateway MDR fee deductions (2.0% standard rate).
  2. `OFF_LEDGER_DEVIATION`: Recurring off-ledger mobility toll/cash deviations.
  3. `INVENTORY_SETTLEMENT`: Kirana chocolate change physical substitutions.

---

## 11. Local AI Explainer & Environment Configuration

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

## 12. Known Limitations & Responsible-Use Boundary

1. **Unobserved Cash Deviations**: The system cannot magically prove pure physical cash handoffs without corroborating circumstantial records (e.g. driver QR receipts or merchant inventory logs). In such cases, the system reports `UNRESOLVED` rather than hallucinating an explanation.
2. **Synthetic Evaluation Context**: The 10,000-record benchmark is generated from realistic mathematical models of Indian retail and mobility transactions; real-world deployment requires enterprise connector integration (SAP, Razorpay API, Finacle).
3. **No Automatic Ledger Mutation**: Human approval of a case in ShadowLedger records an approved settlement action in the audit trail but **never mutates immutable source observation logs**.

---

## 13. Project Structure

```
ShadowLedger/
├── apps/
│   ├── api/                     # FastAPI Backend & Reconstruction Engine
│   │   ├── app/
│   │   │   ├── api/routes/      # Endpoints (/batches, /cases, /metrics, /demo)
│   │   │   ├── domain/          # Scenario library (SCN_01..12), models, enums
│   │   │   ├── engine/          # Reconciler, graph builder, scorer, decision gate
│   │   │   ├── persistence/     # DuckDB 1.4.5 schema & repositories
│   │   │   └── metrics/         # Benchmark evaluator & reporting
│   │   └── tests/               # 51 Unit, property, and adversarial test cases
│   └── web/                     # Next.js 16 Web Dashboard
│       ├── app/                 # Command Center, Cases, Patterns, Benchmark
│       ├── components/          # ValueFlowGraph, EvidenceConfidenceCard, LocalAI
│       └── lib/                 # API client, types, and formatting
├── data/                        # Benchmark artifacts and test batches
├── scripts/                     # Dataset generator & benchmark evaluation harness
├── .github/workflows/ci.yml     # Automated CI/CD pipeline
└── README.md                    # System documentation
```

---

## 14. License & Hackathon Submission Notice

Developed for the **Razorpay AI Buildathon — Track 04 (AI Finance Controller)**.  
MIT License &bull; Free and Open Source.
