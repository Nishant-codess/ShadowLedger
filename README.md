# ShadowLedger

> **Uncertainty-Aware Value-Flow Reconstruction Engine for Finance Operations**
> Built for the **Razorpay AI Buildathon — Track 04: AI Finance Controller**
> Zero-Paid-API Architecture &bull; Local-First &bull; Deterministic Truth Path &bull; Pure Rules Baseline

---

## The Core Problem

Traditional reconciliation tools compare ledger rows looking for exact key/amount matches. When records disagree, they flag an exception and stop.

In real-world commerce:
1. **Multi-Leg Value Flows**: Value moves through cash, non-cash assets, credits, and gateway fees (e.g. ₹98 kirana bill settled with ₹100 cash and ₹2 chocolate as change).
2. **Timing & Structural Gaps**: Transactions split across batches, holidays, and partial refunds.
3. **Off-Ledger Deviations**: Economic reality deviates from the digital record (e.g. ₹150 recorded fare with cash overcharge).
4. **Safety Under Uncertainty**: Reconciling the wrong transaction is dangerous in fintech; the system must quantify evidence confidence and enforce strict decision gates.

ShadowLedger maintains two parallel structures:
- **Official Ledger**: What was recorded in source systems (immutable source observations).
- **Shadow Ledger**: What evidence implies actually occurred, classified across a strict 4-level taxonomy.

---

## 4-Level Event Taxonomy

| Level | Status | Definition | Can Auto-Resolve? |
|---|---|---|---|
| **Level 1** | `OBSERVED` | Directly observed fact from source systems (POS, Bank, Gateway) | Yes (when balanced) |
| **Level 2** | `DERIVED` | Mathematically implied from observed records (e.g. 2% MDR fee) | Yes |
| **Level 3** | `INFERRED_LATENT` | Unrecorded latent event supported by strong connected evidence (refund, credit) | Yes (if safe) |
| **Level 4** | `UNOBSERVED_DEVIATION` | Discrepancy detected where economic reality deviated from ledger | **NEVER** |

---

## Chunk 1: Foundation & Deterministic Baseline

Chunk 1 establishes the financial world and deterministic baseline:

1. **Domain Models**: Typed Pydantic v2 domain contracts (`Observation`, `InventoryMove`, `Event`, `ValueFlow`, `Hypothesis`, `Decision`, `Case`, `PatternCluster`).
2. **Economic Event Scenario Library**: 12 authoritative scenarios (`SCN_01` to `SCN_12`) acting as the single source of truth for synthetic data generation, ground truth, testing, and evaluation.
3. **Deterministic Reconciler**: Pure rule-based engine executing:
   - Connected component entity resolution across shared keys (`order_id`, `payment_id`, `ride_id`, `batch_ref`)
   - Exact ID and amount matching
   - Fee-balanced reconciliation (Gross - 2% fee = Net settlement)
   - Non-cash inventory change settlement (Chocolate change)
   - Duplicate broadcast detection
   - Transparent reason codes on every outcome
4. **DuckDB 1.5 Persistence**: Fast embedded analytical storage with zero configuration.
5. **FastAPI Backend**: Serving `/health`, `/api/batches/process`, `/api/cases`, `/api/metrics`.
6. **Next.js 16 Web Console**: Dark-mode Command Center dashboard, Exception Queue, and Case Workspace shell.

---

## Quickstart & Local Development

### Prerequisites
- Python 3.12+ (tested on Python 3.12, 3.13)
- Node.js 20.9+
- npm 10+

### Setup & Run
```bash
# 1. Install all dependencies
make install

# 2. Run backend test suite
make test

# 3. Generate 10,000 synthetic multi-source records
make data

# 4. Run baseline evaluation benchmark against hidden ground truth
make benchmark

# 5. Start development servers (Backend :8000, Web :3000)
make dev
```

---

## Baseline Benchmark Results (1,000 Records)

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Metric                     ┃ Value                 ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
│ Total Records Ingested     │ 1,000                 │
│ Deterministic Matches      │ 169                   │
│ Unmatched Exceptions       │ 831                   │
│ Baseline Match Rate        │ 16.90%                │
│ Processing Throughput      │ 223,087.7 records/sec │
│ Total Volume (INR)         │ ₹5,115,097.47         │
│ Explained Volume (INR)     │ ₹3,566,675.58         │
│ Unexplained Residual (INR) │ ₹1,548,421.89         │
│ Processing Time            │ 4.5 ms                │
│ Ground Truth Precision     │ 100.00%               │
│ Ground Truth Recall        │ 24.65%                │
│ Unsafe Auto-Resolutions    │ 0                     │
└────────────────────────────┴───────────────────────┘
```

> **Safety Note**: The deterministic baseline achieves **100.00% precision with 0 unsafe auto-resolutions**. It resolves only what is provable under strict mathematical and identity rules, escalating the remaining ~75% of ambiguous cases into the Exception Queue for value-flow graph reconstruction in Chunk 2.

---

## Project Structure

```
ShadowLedger/
├── Makefile                          # Development and testing workflows
├── README.md                         # Project documentation
├── LICENSE                           # MIT License
├── .gitignore                        # Git exclusion rules
├── .github/
│   └── workflows/
│       └── ci.yml                    # Automated CI pipeline
├── apps/
│   ├── api/                          # FastAPI Backend
│   │   ├── app/
│   │   │   ├── domain/               # Pydantic v2 models, enums, 12 scenarios
│   │   │   ├── engine/               # Normalizer & Deterministic reconciler
│   │   │   ├── persistence/          # DuckDB database manager & repositories
│   │   │   ├── data/                 # Ingestion & batch normalization
│   │   │   ├── metrics/              # Evaluation metrics & reporter
│   │   │   ├── api/                  # Route handlers & schemas
│   │   │   └── main.py               # FastAPI entry point
│   │   ├── tests/                    # Pytest unit & integration tests
│   │   └── pyproject.toml            # Python dependencies & tools config
│   └── web/                          # Next.js 16 Web Application
│       ├── app/                      # Command Center, Exceptions, Case pages
│       ├── lib/                      # Typed API client and utilities
│       ├── styles/                   # Tailwind CSS v4 styles
│       ├── package.json              # Frontend dependencies
│       └── tsconfig.json             # TypeScript configuration
├── scripts/
│   ├── generate_dataset.py           # Synthetic dataset generator CLI
│   └── run_benchmark.py              # Evaluation benchmark harness CLI
└── data/
    ├── generated/                    # Observed synthetic datasets (.gitkeep)
    └── truth/                        # Isolated ground truth files (.gitignore)
```

---

## Verification & Quality Gates

Run all automated quality gates:
```bash
make test        # Pytest test suite (27 tests pass)
make lint        # Ruff Python lint + ESLint TypeScript lint
make typecheck   # Mypy Python typecheck + TSC TypeScript typecheck
```

---

## Roadmap

- [x] **Chunk 1**: Foundation + Financial World + Deterministic Baseline + Web Shell
- [ ] **Chunk 2**: Value-Flow Graph Engine + Latent-Event Hypotheses + Shadow Ledger + Cross-Case Pattern Engine (P0)
- [ ] **Chunk 3**: Graph Visualization (Force Graph) + Case Workspace + Benchmark Harness
- [ ] **Chunk 4**: Hardening + Adversarial QA + Demo Preparation + Documentation Freeze

---

## License

MIT License &bull; Copyright (c) 2026 ShadowLedger Contributors
