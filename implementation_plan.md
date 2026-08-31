# ShadowLedger — Implementation Plan v2 (Revised)

**Razorpay AI Buildathon — Track 04: AI Finance Controller**
**Hard Deadline: September 5, 2026**
**Remaining Time: ~5 days from August 31**

---

## A. Executive Summary

ShadowLedger is a **value-flow reconstruction engine** for financial operations. Rather than asking "which records match?", it asks "what economic events must have happened for the observed records to make sense together?"

The system maintains two parallel financial realities:
- **Official Ledger** — immutable source records exactly as recorded by source systems
- **Shadow Ledger** — inferred economic events backed by structured evidence, scored confidence, and explicit uncertainty

The core technical contribution is a **constraint-driven hypothesis engine** that generates, validates, scores, and gates latent economic events. The LLM is strictly relegated to semantic interpretation and explanation — it never sits in the truth path.

**What makes this different from "AI reconciliation":**
1. Four-level event taxonomy: Observed → Derived → Inferred Latent → **Unobserved Economic Deviation**
2. Case-local value-flow graphs that reason about economic stories, not just row pairs
3. Cross-case pattern discovery that collapses hundreds of tiny exceptions into recurring common patterns
4. Explicit separation of **evidence confidence** from **decision risk**
5. Safety-first: the system says "we don't know" when evidence is insufficient

**The line:**
> "A ledger tells you what was recorded. ShadowLedger investigates what the records imply actually happened."

---

## B. Locked Product Thesis

> ShadowLedger is a finance-ops control system that reconstructs economic value flows from imperfect records. It maintains an Official Ledger of what was recorded and a Shadow Ledger of evidence-backed inferred events. Its core engine detects value-flow violations, tests hidden-event hypotheses, resolves only when safe, discovers recurring patterns across apparently unrelated exceptions, and surfaces micro-leakage and likely common causes across a batch.

---

## C. Problem and User/Stakeholder Model

### The Real Problem
Financial systems record transactions. Real commerce contains value movements the ledger does not represent: informal change given as inventory items, store credits applied against future purchases, off-ledger cash payments that deviate from recorded fares, partial refunds, batch-level fee adjustments, duplicated entries, timing drift across systems.

These create discrepancies that individually seem insignificant but collectively represent material financial risk. Traditional reconciliation treats this as a row-matching problem. The result is thousands of "unmatched" records that humans must investigate one by one, with no systematic way to understand the *economic story* behind the mismatch.

### Stakeholders

| Stakeholder | Pain | ShadowLedger Value |
|---|---|---|
| Merchant / business owner | Small discrepancies accumulate, hard to trace | Quantified unexplained value, recurring leakage patterns |
| Finance operator | Hours comparing files, investigating edge cases | Evidence-backed case summaries, fewer manual investigations |
| Finance controller | Needs confidence that automation is safe | Explicit confidence gates, audit trail, held-out metrics |
| Platform / payment provider | Large-scale merchants generate messy multi-source data | Reusable investigation layer on top of reconciliation |
| Auditor | Needs to know *why* a number was resolved | Immutable evidence links and explanation chain |

---

## D. Exact MVP

### P0 — Must exist for submission

| Feature | Description |
|---|---|
| Batch ingestion | Load 50+ records (target 10,000), validate schema |
| Normalization | Canonical event schema, timestamps, amounts, entity IDs, inventory valuation |
| Deterministic reconciliation | Exact + rule-based matching baseline with reason codes |
| Exception miner | Detect mismatches, orphans, duplicates, timing gaps |
| Case-local value-flow graph | Per-case graph from relevant connected evidence (not giant global graph) |
| Latent-event engine | ≥6 hypothesis types including OFF_LEDGER_DEVIATION |
| Shadow Ledger | Inferred events stored separately with four-level event taxonomy |
| Evidence confidence | Separate scoring of how strongly evidence supports a hypothesis |
| Decision risk gate | Applies materiality, contradiction, action risk independently from confidence |
| **Cross-case pattern engine** | Collapse many exceptions into recurring patterns / likely common causes + micro-leakage aggregation |
| Audit trail | Evidence, reasoning, version, decision for every inference |
| Metrics | Match rate, precision, recall, throughput, value explained, unsafe auto-resolutions |
| Scenario library | 12 defined scenarios as single source for data, benchmark, tests, demo |
| Web UI | Command Center + Case Workspace + Value-Flow Graph (3 core experiences) |
| Synthetic data generator | Reproducible batches with hidden ground truth from scenario library |
| Evaluation harness | Held-out benchmark, adversarial test suite |

### P1 — If time allows

| Feature | Description |
|---|---|
| LLM explanation layer | Natural-language case summaries grounded in structured evidence (Qwen3 8B via Ollama) |
| Expanded UI pages | Dedicated batch explorer, dedicated audit log page |
| Deeper analytics | Per-merchant leakage fingerprint, temporal drift analysis |

### P2 — Explicitly cut

| Feature | Reason |
|---|---|
| What-if / counterfactual simulation | Scope risk |
| Cross-batch drift detection | Out of scope for hackathon |
| Handmade Rakhi / complex supply-chain scenarios | Requires entire additional economic model (transfer pricing, profit share) |
| Active learning queue | Too complex for remaining time |
| Voice / chat interface | No product value for judge demo |
| Mobile app | Wrong interaction surface |
| Multi-agent swarm | Unnecessary complexity |
| Fine-tuning | Out of scope |
| Real payment integration | Not needed for synthetic demo |

---

## E. Proposed Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Web Frontend (Next.js 16)                   │
│   Command Center  │  Case Workspace  │  Value-Flow Graph View   │
└─────────────────────────────┬────────────────────────────────────┘
                              │ HTTP / REST
┌─────────────────────────────▼────────────────────────────────────┐
│                       FastAPI Backend                              │
│                                                                   │
│  OBSERVED DATA                                                    │
│       ↓                                                           │
│  NORMALIZATION (dates, currencies, signs, inventory valuation)    │
│       ↓                                                           │
│  DETERMINISTIC RECONCILIATION (hard IDs, amount+time, refs)       │
│       ↓                                                           │
│  EXCEPTION MINING (residuals, orphans, duplicates, timing)        │
│       ↓                                                           │
│  CASE-LOCAL VALUE-FLOW GRAPH (NetworkX per case, not global)      │
│       ↓                                                           │
│  LATENT EVENT ENGINE                                              │
│       ┌──────────────────────────────────────┐                    │
│       │ Evidence       │ Constraints          │                    │
│       │ Temporal       │ Entity relations     │                    │
│       │ Value conserv. │ Behavioral patterns  │                    │
│       └──────────────────────────┬───────────┘                    │
│       ↓                                                           │
│  HYPOTHESIS RANKER → EVIDENCE CONFIDENCE                          │
│       ↓                                                           │
│  DECISION RISK GATE                                               │
│       ├── evidence confidence                                     │
│       ├── contradiction severity                                  │
│       ├── financial materiality                                   │
│       └── action risk                                             │
│       ↓                                                           │
│  ┌──────────┬──────────┬──────────┐                               │
│  │AUTO      │HUMAN     │UNRESOLVED│                               │
│  │RESOLVE   │REVIEW    │          │                               │
│  └──────────┴──────────┴──────────┘                               │
│       ↓                                                           │
│  SHADOW LEDGER (append-only inferred events)                      │
│       ↓                                                           │
│  CROSS-CASE PATTERN ENGINE (P0)                                   │
│       ↓                                                           │
│  MICRO-LEAKAGE / RECURRING PATTERN AGGREGATION                    │
│       ↓                                                           │
│  AUDIT + METRICS + UI                                             │
│                                                                   │
│  ┌─────────────────────────────────────────────┐                  │
│  │        LLM Adapter (Ollama — P1, optional)  │                  │
│  │  semantic norm │ label suggest │ explanation │                  │
│  │         ↓               ↓            ↓      │                  │
│  │         └───── STRICTLY VALIDATED ───┘       │                  │
│  │              ↓                               │                  │
│  │         CORE ENGINE (LLM never in truth path)│                  │
│  └─────────────────────────────────────────────┘                  │
│                                                                   │
│  ┌─────────────────────────────────────────────┐                  │
│  │         DuckDB 1.4.5 LTS (embedded)         │                  │
│  │   Observations + Shadow Events + Audit       │                  │
│  └─────────────────────────────────────────────┘                  │
└───────────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Monolithic deployment** — Single FastAPI process + single Next.js dev server. No microservices.
2. **Embedded database** — DuckDB runs in-process. No external database server.
3. **LLM is P1 and optional** — The entire pipeline runs without an LLM. The LLM adapter is disabled by default. The deterministic engine is the product.
4. **Deterministic core** — All arithmetic, matching, scoring, constraints, and decisions use deterministic Python. Reproducible from the same seed.
5. **Case-local reasoning** — Global data lives in DuckDB. Reasoning graphs exist only for the relevant case/subgraph. NetworkX is not "the financial graph" — it is a case-investigation tool.
6. **Local-first** — Works offline after initial setup. No cloud dependencies at runtime.

---

## F. Technology Choices and Alternatives

### Backend

| Component | Choice | Version | License | Why | Rejected Alternative | Why Rejected |
|---|---|---|---|---|---|---|
| Language | Python 3.12+ | 3.12.x | PSF | Fastest iteration for data + graph + eval | Go, Rust | Build speed; data science ecosystem |
| API Framework | FastAPI | >=0.141.0,<0.142.0 | MIT | Async, typed, auto-docs | Flask | Lacks validation/typing |
| Data Validation | Pydantic v2 | 2.x | MIT | Native FastAPI, strict contracts | dataclasses | No validation |
| Database | DuckDB | **1.4.5 LTS** | MIT | Embedded OLAP, zero-config, stable | SQLite, PostgreSQL | SQLite poor at analytics; PG needs a server |
| Graph | NetworkX | 3.6.x | BSD | Case-local subgraph reasoning | Neo4j | Requires server/ops |
| ML/Stats | scikit-learn | 1.x | BSD | Clustering for pattern detection | — | Standard |
| Linting | ruff | latest | MIT | Fast, single tool | flake8+black | Slower, multiple tools |
| Type Checking | mypy | latest | MIT | Pre-runtime type safety | pyright | mypy more established |
| Testing | pytest | latest | MIT | Fixtures, parameterization | unittest | Less ergonomic |

### Frontend

| Component | Choice | Version | License | Why | Rejected Alternative | Why Rejected |
|---|---|---|---|---|---|---|
| Framework | Next.js (App Router) | 16.x | MIT | Full React ecosystem, professional UI | Streamlit | Cannot produce premium finance-console UX; looks like 500 other submissions |
| Language | TypeScript | 5.1+ | Apache 2.0 | Type safety, catch errors at build | JavaScript | Too error-prone for demo-day |
| Node.js | Node.js | **20.9+** (maintained LTS) | MIT | Next.js 16 requirement | — | — |
| Styling | Tailwind CSS v4 + shadcn/ui | 4.x / latest | MIT | Rapid, dark-mode-ready | Vanilla CSS | Too slow for remaining time |
| Charts | Recharts | 2.x | MIT | Simple React-native charting | Chart.js | Recharts simpler in React |
| Graph Visualization | react-force-graph-2d | latest | MIT | Canvas-based, performant, force-directed | D3 manual | react-force-graph faster to integrate |
| Linting | **ESLint CLI or Biome** | latest | MIT | Next.js 16 removed `next lint`; must use direct ESLint/Biome | `next lint` | Removed in Next.js 16 |

> [!IMPORTANT]
> **Next.js 16 CI correction**: `next lint` has been removed in Next.js 16. The CI pipeline must invoke ESLint CLI directly (e.g., `npx eslint .`) or use Biome. `next build` no longer performs linting automatically.

### LLM (P1 — Optional)

| Component | Choice | Version | License | Why |
|---|---|---|---|---|
| LLM Runtime | Ollama | 0.33.x | MIT | One-command local LLM |
| LLM Model | Qwen3 8B (fallback: 4B) | — | Apache 2.0 | Strong structured output, Apache license, runs on 16GB |

### Cost Verification

| Dependency | Cost | Status |
|---|---|---|
| Python + all libraries | Free/OSS | ✅ |
| Next.js + all npm packages | Free/OSS | ✅ |
| DuckDB 1.4.5 LTS | Free/OSS (MIT) | ✅ |
| Ollama | Free/OSS (MIT) | ✅ |
| Qwen3 8B | Free/OSS (Apache 2.0) | ✅ |
| GitHub Actions (public repo) | Free, unlimited standard minutes | ✅ |

**Total runtime cost: ₹0** ✅

---

## G. Data Model

### Four-Level Event Taxonomy

This is a core conceptual distinction that must exist in the domain model:

| Level | Name | Definition | Can Auto-Resolve? |
|---|---|---|---|
| 1 | **OBSERVED** | Something physically/logically present in a source record | N/A (it's a fact) |
| 2 | **DERIVED** | Something mathematically implied by observed events (e.g., fee = gross − net) | Yes, if deterministic |
| 3 | **INFERRED_LATENT** | Something not recorded but strongly supported by evidence (e.g., refund, inventory-as-change) | Yes, if confidence + constraints pass |
| 4 | **UNOBSERVED_DEVIATION** | Something for which the system detects a discrepancy pattern but cannot establish the hidden event directly (e.g., off-ledger cash payment) | **NEVER** — always HUMAN_REVIEW or UNRESOLVED |

### Core Domain Objects (Pydantic v2)

```python
class EventStatus(str, Enum):
    OBSERVED = "observed"
    DERIVED = "derived"
    INFERRED_LATENT = "inferred_latent"
    UNOBSERVED_DEVIATION = "unobserved_deviation"

class HypothesisType(str, Enum):
    REFUND = "refund"
    FEE_ADJUSTMENT = "fee_adjustment"
    PARTIAL_SETTLEMENT = "partial_settlement"
    INVENTORY_SETTLEMENT = "inventory_settlement"
    STORE_CREDIT = "store_credit"
    DUPLICATE_REVERSAL = "duplicate_reversal"
    TIMING_OFFSET = "timing_offset"
    MISSING_PAYMENT = "missing_payment"
    OFF_LEDGER_DEVIATION = "off_ledger_deviation"       # NEW — Uber/cab case
    UNKNOWN = "unknown"

class ValueType(str, Enum):
    CASH = "cash"
    INVENTORY = "inventory"
    CREDIT = "credit"
    OBLIGATION = "obligation"

class DecisionType(str, Enum):
    AUTO_RESOLVE = "auto_resolve"
    HUMAN_REVIEW = "human_review"
    UNRESOLVED = "unresolved"
```

```python
class Observation:
    observation_id: str             # stable deterministic hash
    source_system: str              # "pos", "bank", "gateway", "inventory", "ride_platform"
    source_record_id: str
    raw_payload: dict               # original record preserved verbatim
    event_type: EventType
    amount: Decimal                 # normalized, signed
    currency: str                   # "INR"
    timestamp: datetime             # UTC-normalized
    entity_ids: dict                # merchant_id, customer_id, order_id, driver_id, etc.
    description: str                # raw text
    batch_id: str
    ingested_at: datetime

class InventoryMove:
    """Expanded inventory valuation for the chocolate/change case."""
    move_id: str
    observation_id: str
    sku: str | None
    item_description: str
    quantity: Decimal
    unit_cost: Decimal | None       # cost to merchant
    retail_value: Decimal | None    # price to customer
    valuation_basis: str            # "retail" | "cost" | "estimated" | "unknown"
    # The ValueFlow edge must know whether ₹2 means retail-value or cost

class Event:
    event_id: str
    status: EventStatus             # OBSERVED | DERIVED | INFERRED_LATENT | UNOBSERVED_DEVIATION
    event_type: EventType
    amount: Decimal
    currency: str
    timestamp: datetime
    entity_ids: dict
    source_observation_ids: list[str]
    confidence: float | None        # None for OBSERVED / DERIVED
    hypothesis_type: HypothesisType | None
    contradiction_ids: list[str]
    batch_id: str

class ValueFlow:
    flow_id: str
    source_event_id: str
    target_event_id: str
    amount: Decimal
    value_type: ValueType           # CASH | INVENTORY | CREDIT | OBLIGATION
    direction: str                  # "transfer", "settles", "refunds", "consumes"
    evidence_ids: list[str]
    valuation_basis: str | None     # for inventory flows: "retail" | "cost" | "estimated"

class Hypothesis:
    hypothesis_id: str
    hypothesis_type: HypothesisType
    case_id: str
    generated_event: Event
    evidence_ids: list[str]
    contradiction_ids: list[str]
    # --- Scoring (evidence-only) ---
    evidence_coverage: float
    amount_consistency: float
    temporal_consistency: float
    entity_consistency: float
    business_rule_fit: float
    assumption_cost: float
    contradiction_cost: float
    evidence_score: float           # combined evidence score
    evidence_confidence: float      # calibrated from evidence_score
    # --- Risk (separate from evidence) ---
    financial_impact: Decimal       # absolute value at stake
    constraints_satisfied: list[str]
    constraints_violated: list[str]
    can_auto_resolve: bool          # False for UNOBSERVED_DEVIATION, always

class Decision:
    case_id: str
    decision: DecisionType
    winning_hypothesis_id: str | None
    reason_codes: list[str]
    evidence_ids: list[str]
    # --- Separate dimensions ---
    evidence_confidence: float
    contradiction_severity: float
    financial_materiality: float    # how much money is at risk
    action_risk: str                # "low" | "medium" | "high"
    # ---
    engine_version: str
    model_version: str | None
    decided_at: datetime

class Case:
    case_id: str
    batch_id: str
    observation_ids: list[str]
    hypotheses: list[Hypothesis]
    decision: Decision | None
    residual_amount: Decimal
    financial_impact: Decimal
    pattern_cluster_id: str | None
    scenario_id: str | None         # links back to scenario library

class PatternCluster:
    """Cross-case pattern — P0."""
    cluster_id: str
    batch_id: str
    case_ids: list[str]
    pattern_signature: str          # e.g., "same_merchant+inventory_settlement+amount_band_1_5"
    exception_count: int
    total_value_at_risk: Decimal
    likely_common_cause: str      # NOT "root cause" — use cautious language unless causal evidence exists
    evidence_strength: float
```

### Storage Strategy (DuckDB 1.4.5 LTS)

```
observations          — source records, immutable, append-only
inventory_moves       — expanded inventory valuation data
events                — normalized events (all four levels)
value_flows           — edges in case-local graphs
hypotheses            — candidate latent events with evidence scores
decisions             — gate outcomes per case
cases                 — investigation units
pattern_clusters      — aggregated recurring patterns (P0)
audit_log             — every inference with full provenance
batch_metadata        — batch-level summary and config
```

Single `.duckdb` file. No external database. Tables created on first run.

---

## H. Core Reasoning Pipeline

### Stage 1 — Deterministic Baseline Reconciliation

```
match_score = weighted evidence score

Hard evidence:
  same transaction/order/payment ID        +1.00
  exact amount                             +0.30
  compatible event-time window (±24h)      +0.15
  same merchant/customer/entity            +0.15
  known causal ordering                    +0.10

Rules:
  if hard-ID link exists AND consistency checks pass → MATCH
  else → candidate set for further investigation
```

**No LLM calls in this stage.**

### Stage 2 — Exception Mining

Compute residuals for every matched/unmatched cluster:
- Expected value − explained value = **residual**
- Identify: orphan records, amount discrepancies, timing gaps, duplicate patterns
- Residuals > materiality threshold → create **Case** for investigation

### Stage 3 — Case-Local Value-Flow Graph Construction

For each Case:
1. Query DuckDB for the relevant connected observations
2. Extract only the related evidence (same merchant, customer, order, time window)
3. Build a **small, focused NetworkX graph** for this case
4. Nodes = events (observed + any candidates)
5. Edges = value flows (cash, inventory, credit, obligation)

> [!IMPORTANT]
> The graph is **case-local**, not a giant global reasoning graph. Global data lives in DuckDB. NetworkX is a case-investigation tool. This is faster, simpler, and makes graphs more meaningful for visualization.

### Stage 4 — Latent-Event Hypothesis Generation

For each case, generate candidates from the **hypothesis library**:

| Hypothesis Type | Precondition | Example | Can Auto-Resolve? |
|---|---|---|---|
| REFUND | Payment exists, settlement < payment | ₹10K payment, ₹8.5K settlement → ₹1.5K refund | Yes |
| FEE_ADJUSTMENT | Settlement ≠ capture by known % | ₹1000 → ₹980 (2% gateway fee) | Yes |
| PARTIAL_SETTLEMENT | One payment, multiple settlement records | Payment split across batches | Yes |
| INVENTORY_SETTLEMENT | Cash shortfall + inventory movement nearby | ₹100 paid for ₹98, ₹2 chocolate given as change | **Conditional** (see below) |
| STORE_CREDIT | Cash shortfall + customer credit issued | ₹2 carried to future purchase | Yes |
| DUPLICATE_REVERSAL | Two records with same amount/entity/time | Same event recorded twice | Yes |
| TIMING_OFFSET | Records in different batches within tolerance | Settlement in next-day batch | Yes |
| MISSING_PAYMENT | Settlement exists but no source payment | Orphan settlement | Yes (with strong evidence) |
| **OFF_LEDGER_DEVIATION** | Fare/price discrepancy + no digital trace | ₹150 fare, possible ₹200 actual payment | **NEVER** |

**INVENTORY_SETTLEMENT auto-resolution conditions**: Auto-resolve ONLY when ALL of the following hold: (1) the inventory movement is explicitly linked to the transaction/customer/order in the data, (2) the valuation basis is known (not "estimated" or "unknown"), (3) the amount equation closes (residual ≤ tolerance), and (4) no contradicting evidence exists. Otherwise → HUMAN_REVIEW or UNRESOLVED. Merely seeing "one chocolate disappeared near that timestamp" is NOT sufficient for auto-resolution.

**OFF_LEDGER_DEVIATION** is a distinct concept: the system detects that economic reality may have deviated from the recorded transaction, but no corresponding **direct** transaction record exists. This can NEVER auto-resolve.

> [!IMPORTANT]
> **"No direct trace" ≠ "no evidence."** The absence of a direct transaction record does not mean there is no evidence at all. Indirect evidence can still exist and should be surfaced:
> - Ride timing and route data
> - Driver/customer payment-mode history
> - Complaint or dispute signals
> - Repeated behavioral patterns across a cohort
> - Synthetic external transaction traces
>
> The system should use language such as:
> - *Directly observed extra payment*: **NO**
> - *Supporting indirect evidence*: **YES** (with specifics)
> - *Inference*: Possible off-ledger deviation
>
> This distinction must be enforced in both the data model (`Hypothesis.evidence_ids` may contain indirect evidence observations) and the UI (the Case Workspace must clearly separate direct vs. indirect evidence).

OFF_LEDGER_DEVIATION produces a shadow hypothesis with estimated range and routes to HUMAN_REVIEW or UNRESOLVED depending on indirect evidence strength.

### Stage 5 — Evidence Scoring (Separate from Risk)

```
evidence_score(H) =
    w1 * evidence_coverage          (what fraction of involved records support this?)
  + w2 * amount_consistency         (does the math add up?)
  + w3 * temporal_consistency       (is the timing plausible?)
  + w4 * entity_consistency         (same merchant/customer/order chain?)
  + w5 * business_rule_fit          (does this match known commercial patterns?)
  - w6 * assumption_cost            (how many things did we assume?)
  - w7 * contradiction_cost         (is there contradicting evidence?)

evidence_confidence = calibrated(evidence_score)
```

> [!IMPORTANT]
> **Financial risk is NOT part of evidence confidence.** Whether an event is worth ₹10 or ₹10 lakh doesn't change how confident we are that the event occurred. It changes what we are *allowed to do* about it. This separation is architecturally critical.

Weights are selected using only the **calibration set** (60%); thresholds selected using **validation set** (20%); held-out test data (20%) remains untouched until final evaluation.

### Stage 6 — Decision Risk Gate

The decision gate applies **four independent dimensions**:

```
INPUTS:
  1. evidence_confidence    (from Stage 5)
  2. contradiction_severity (hard contradictions?)
  3. financial_materiality  (how much money is at stake?)
  4. hypothesis_type        (OFF_LEDGER_DEVIATION can never auto-resolve)

DECISION LOGIC:
  if hypothesis_type == OFF_LEDGER_DEVIATION:
      → HUMAN_REVIEW or UNRESOLVED (never AUTO_RESOLVE)

  elif evidence_confidence >= AUTO_THRESHOLD
       AND contradiction_severity == NONE
       AND financial_materiality <= MATERIALITY_LIMIT:
      → AUTO_RESOLVE

  elif evidence_confidence >= REVIEW_THRESHOLD:
      → HUMAN_REVIEW

  else:
      → UNRESOLVED
```

High-value cases (financial_materiality > threshold) are **always** HUMAN_REVIEW regardless of confidence. This is a safety net.

### Stage 7 — Cross-Case Pattern Engine (P0)

After individual cases are evaluated, aggregate exceptions by structural signatures:
- Same merchant + same hypothesis type + similar amount band → recurring pattern
- Same batch/time window + many exceptions → likely common cause
- Same operator + repeated micro-discrepancies → behavioral fingerprint

Output: `PatternCluster` objects with:
- Exception count ("412 micro-events")
- Total value at risk ("₹3.7L unexplained")
- Likely common cause description ("3 recurring operational patterns")
- Evidence strength

> [!IMPORTANT]
> **Cautious causal language**: Unless we have actual causal evidence, use "recurring pattern" or "likely common cause" — NOT "root cause." Saying "412 exceptions share a common structural pattern" is defensible. Saying "this system failure caused all 412 exceptions" requires stronger evidence than structural similarity. This protects us if a Razorpay engineer challenges our causal claims.

This is **P0** because it is what transforms us from "AI reconciliation" into "a system that discovers hidden economic patterns behind apparently unrelated exceptions."

---

## I. LLM Strategy

### Priority: P1 — Optional

The deterministic engine is the product. The LLM is a useful enhancement but not required for the system to produce valid financial decisions.

**P0**: Deterministic engine works completely without any LLM.
**P1**: Qwen3 8B explanation layer adds narrative summaries.

### Where AI May Be Used (When Available)

| Task | LLM? | Why |
|---|---|---|
| Parse semantic descriptions | YES (P1) | Messy natural language benefits from understanding |
| Normalize merchant/item labels | YES (P1) | Synonyms, abbreviations, multilingual |
| Suggest candidate event types | YES, constrained (P1) | Model proposes from fixed enum; code validates |
| Narrative explanation of a case | YES (P1) | Grounded on structured evidence, citing record IDs |

### Where AI IS NOT Used

| Task | LLM? | Why |
|---|---|---|
| Arithmetic | NO | Python `Decimal` is authoritative |
| Match scoring | NO | Deterministic scoring = reproducible evaluation |
| Constraint satisfaction | NO | Core novelty implemented in code |
| Evidence confidence | NO | Calibration and scoring belong to engine |
| Final decision | NO | Engine policy only |

### LLM Interface Contract (P1)

```
POST /api/llm/explain-case
INPUT:  structured CaseEvidence JSON
OUTPUT: strict JSON {
  "summary": "...",
  "hypothesis": "REFUND | FEE | ...",
  "evidence_ids": ["obs_123"],
  "contradiction_ids": [],
  "confidence_language": "high | medium | low"
}
```

Backend rejects: unknown IDs, unsupported event types, numerical contradictions. Falls back to "explanation unavailable" on failure.

### LLM Failure Mode

App continues via deterministic-only paths. Case explanations show "LLM unavailable — deterministic evidence shown." No financial decision affected.

---

## J. Frontend/Application Structure

### Product Format: Desktop-First Web Application (Next.js 16)

### Reduced to 3 P0 Experiences

> [!IMPORTANT]
> **Frontend scope reduction**: Instead of 7 separate pages, we build 3 excellent experiences. Audit is a tab inside Case Workspace. Pattern analysis is a panel inside Command Center. Batch Explorer is a dropdown/table, not a separate page. This gives us more time to make the hero case spectacular.

#### 1. Command Center (Homepage)

- Batch health: total records, processed, resolved, review, unresolved
- Key metrics cards: match rate, precision, throughput, value explained
- "Process Batch" action button
- Official value vs. explained value vs. unexplained value (stacked bar or sankey)
- **Pattern panel** (embedded): recurring patterns table, "N exceptions → 1 likely common cause"
- Micro-leakage summary: estimated value at risk
- Batch selector (dropdown for multiple batches)

#### 2. Case Workspace (Hero Experience)

A single, dense workspace page with **tabs**:

**Tab: Evidence**
- **Official Ledger** panel: source records exactly as recorded
- **Shadow Ledger** panel: inferred events with confidence and status
- Side-by-side comparison
- Observation details with amounts, timestamps, entity IDs
- Contradictions highlighted in red
- Evidence confidence score (visual indicator)
- Decision gate outcome with reason codes
- For inventory cases: valuation breakdown (cost vs. retail vs. estimated)
- "Approve" / "Escalate" demo buttons

**Tab: Value-Flow Graph**
- Force-directed graph (react-force-graph-2d)
- Observed events: solid nodes
- Inferred events: dashed/glowing nodes
- Unobserved deviations: pulsing red outline
- Edges labeled with amount + flow type (cash, inventory, credit)
- Interactive: click node to see details
- **This is the "wow" moment**

**Tab: Audit Trail**
- Chronological log for this case
- Evidence IDs, engine version, model version, timestamp, decision reasoning

#### 3. Exception Queue

- Prioritized list of cases by financial impact
- Filter by decision type (AUTO_RESOLVE, HUMAN_REVIEW, UNRESOLVED)
- Color-coded severity (green/amber/red)
- Click-through to Case Workspace
- Quick-stats summary at top

### Design Aesthetic
- Dark mode primary (finance/trading terminal feel)
- Accent colors: emerald green (resolved), amber (review), red (unresolved), blue (observed), purple (inferred), pulsing red (unobserved deviation)
- Inter font family
- Dense, data-rich layouts — no chatbot, no empty space
- Subtle animations on state transitions
- Glassmorphism cards for metrics

---

## K. Evaluation Strategy

### Dataset Split

```
CALIBRATION SET:    60%    — used to select score weights and thresholds
VALIDATION SET:     20%    — used once to select final threshold set
HELD-OUT TEST:      20%    — untouched until final evaluation
ADVERSARIAL SUITE:  separate, manually curated "looks plausible but wrong"
```

> [!IMPORTANT]
> We are NOT training an ML model. We are calibrating a deterministic scoring engine. "Calibration set" is the correct term.

Score weights are selected using only the calibration set. Thresholds are selected using validation. Held-out test data remains untouched until final evaluation.

### Required Metrics

| Metric | Definition | Safety Target |
|---|---|---|
| Throughput | Records/second on demo hardware | Measure honestly, report hardware |
| Baseline match rate | Records matched by deterministic engine | Report without overfit |
| Auto-resolution precision | Correct auto-resolves / total auto-resolves | **Target ≥97% if achievable without artificially reducing coverage** |
| Auto-resolution coverage | Auto-resolved / all resolvable cases | Report alongside precision |
| Unsafe auto-resolutions | Wrong cases auto-resolved | As close to 0 as possible |
| Exception quality | Correctly escalated / truly ambiguous | Target ≥95% on adversarial negatives |
| Value explained | Resolved discrepancy value / total discrepancy value | Report by scenario family |
| Pattern compression | Individual exceptions → recurring pattern clusters | Show concrete example |
| **OFF_LEDGER detection rate** | OFF_LEDGER_DEVIATION hypotheses generated / true off-ledger events in ground truth | Measure on SCN_08/09/10 |
| **OFF_LEDGER false accusation rate** | Incorrect off-ledger hypotheses / total off-ledger hypotheses generated | As close to 0 as possible |
| **Indirect evidence surfacing** | OFF_LEDGER cases where indirect evidence was correctly identified / total off-ledger cases | Report honestly |

> [!IMPORTANT]
> **97% is a safety target, not an assumed result.** We optimize for safe automation, not maximum automation. A result of "99.2% precision at 18.7% coverage" is legitimate and defensible. Report both dimensions honestly. In fintech, blindly maximizing coverage is dangerous — and saying so is a strong story.

---

## L. Economic Event Scenario Library

This is the **single source** for synthetic data generation, benchmark evaluation, test fixtures, and demo cases. Every scenario has:
- Observed data specification
- Hidden ground truth
- Allowed hypothesis types
- Expected engine behavior
- Expected decision
- Expected UI outcome

| ID | Scenario | Ground Truth | Purpose |
|---|---|---|---|
| SCN_01 | Normal settlement | One-to-one amount/ID/time match | Baseline |
| SCN_02 | Partial refund | Refund explains part of mismatch | Latent event |
| SCN_03 | Fee/adjustment | Gross and net differ by known fee | Accounting rule |
| SCN_04 | **₹100 → ₹98 + chocolate (kirana)** | Non-cash settlement via inventory | **Hero A** |
| SCN_05 | Store credit carry-forward | Obligation moves to future purchase | Temporal obligation |
| SCN_06 | Next-day settlement (timing offset) | Settlement in different batch | Temporal robustness |
| SCN_07 | Duplicate/reversal | Same event appears twice | Deduplication |
| SCN_08 | **₹150 fare + ₹50 digital extra payment** | Hidden truth: passenger paid ₹200 cash, ₹50 off-ledger; digital trace of extra ₹50 exists in synthetic external payment log. Engine never sees truth directly — must infer from evidence. | **Hero B (evidence found)** |
| SCN_09 | **₹150 fare, cash-only deviation** | Hidden truth: passenger paid ₹200 cash, ₹50 off-ledger; NO digital record of extra payment exists. Truth file records the actual ₹200 payment event, but engine has zero direct transaction evidence for the extra ₹50. | **Hero B (no evidence → UNRESOLVED)** |
| SCN_10 | **Repeated micro-deviation pattern** | Hidden truth: across N rides, drivers systematically received ₹30–₹70 above recorded fare. Truth file contains per-ride actual amounts. Engine sees only official fares + statistical anomaly signals across the cohort. | **Hero C (pattern collapse)** |
| SCN_11 | One upstream cause → many exceptions | Batch adjustment affects many transactions | Global reasoning |
| SCN_12 | Deceptive near-match (adversarial) | Plausible but wrong candidate | **Safety benchmark** |

### Three Hero Demo Cases

**Hero A — Kirana Inventory Settlement**
- ₹100 → ₹98 goods + ₹2 chocolate
- Shows: inventory valuation (cost vs. retail), value-flow graph with inventory edge
- Decision: AUTO_RESOLVE (strong evidence, low value)

**Hero B — Ride-Hailing Off-Ledger Deviation**
Three evidence situations:
1. SCN_08: Digital extra payment found → HUMAN_REVIEW (shadow hypothesis with evidence)
2. SCN_09: Cash-only, no trace → UNRESOLVED (possible deviation, insufficient evidence)
3. SCN_10: Repeated pattern across 5,000 rides → pattern cluster detected

This demonstrates: direct evidence → indirect evidence → statistical pattern

**Hero C — Pattern Collapse**
- 400+ tiny anomalies across a batch
- System collapses them into 3 recurring operational patterns
- Shows micro-leakage aggregation and estimated value at risk

---

## M. Testing Strategy

### Unit Tests (pytest)
- All domain models validate correctly (Pydantic v2)
- Every hypothesis type: at least 2 cases (positive + negative)
- Deterministic reconciliation: correct matches on known fixtures
- Scoring function: expected values for known inputs
- Decision gate: correct decision for known confidence/risk combinations
- OFF_LEDGER_DEVIATION: NEVER auto-resolves (explicit test)
- Inventory valuation: cost vs. retail distinction preserved
- Evidence confidence vs. decision risk: independent dimensions

### Integration Tests
- Full pipeline from CSV ingestion to decisions
- Benchmark produces deterministic output with same seed
- LLM adapter degrades gracefully when unavailable
- API endpoints return correct schemas and status codes
- Pattern engine produces clusters from seeded scenarios

### Adversarial Tests
- ≥25 cases where a plausible hypothesis is wrong
- Deceptive near-matches must NOT auto-resolve
- Conflicting evidence → HUMAN_REVIEW or UNRESOLVED
- Missing evidence → no confident hypothesis
- Duplicate records → not double-counted
- High-value case → HUMAN_REVIEW regardless of confidence

### Smoke Test
- API starts and `/health` returns 200
- Frontend builds and serves
- Small fixture batch processes end-to-end

---

## N. Git/GitHub Strategy

### Repository Setup
- **Name**: `shadowledger`
- **Visibility**: Public
- **Description**: "Uncertainty-aware value-flow reconstruction for finance operations"
- **License**: MIT

### Simplified Four-Commit Workflow

No unnecessary branch proliferation. Each chunk:

```
main
│
├── chunk-1 work (local commits)
│   └── squash → commit 1 → push → tag v1.0
│
├── chunk-2 work (local commits)
│   └── squash → commit 2 → push → tag v2.0
│
├── chunk-3 work (local commits)
│   └── squash → commit 3 → push → tag v3.0
│
└── chunk-4 work (local commits)
    └── squash → commit 4 → push → tag v4.0
```

### Commit Messages

```
feat(foundation): data model, scenario library, synthetic generator, deterministic baseline
feat(engine): value-flow graph, latent-event hypotheses, shadow ledger, pattern engine
feat(app): web console, case workspace, graph visualization, evaluation harness
feat(release): hardening, adversarial QA, CI/CD, demo preparation, documentation
```

### .gitignore

```
__pycache__/ *.pyc .venv/ *.egg-info/ dist/ build/
node_modules/ .next/ out/
data/generated/*.parquet data/generated/*.csv data/truth/ *.duckdb *.duckdb.wal
.env .env.local
.vscode/ .idea/ .DS_Store
models/
```

---

## O. CI/CD Strategy

### GitHub Actions CI

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -e "./apps/api[dev]"
      - run: ruff check apps/api
      - run: mypy apps/api --ignore-missing-imports
      - run: pytest apps/api/tests -q

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20.9'
      - run: cd apps/web && npm ci
      - run: cd apps/web && npx eslint .        # NOT next lint (removed in Next.js 16)
      - run: cd apps/web && npx tsc --noEmit    # typecheck
      - run: cd apps/web && npm run build

  smoke:
    needs: [backend, frontend]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -e "./apps/api[dev]"
      - run: python scripts/generate_dataset.py --rows 100 --seed 42
      - name: End-to-end smoke test (not just /health)
        run: |
          timeout 60 python -c "
          import uvicorn, threading, time, urllib.request, json

          # 1. Start API server
          t = threading.Thread(target=lambda: uvicorn.run('apps.api.app.main:app', port=8000), daemon=True)
          t.start(); time.sleep(3)

          # 2. Health check
          r = urllib.request.urlopen('http://localhost:8000/health')
          assert r.status == 200, 'Health check failed'

          # 3. Ingest the generated 100-row dataset
          req = urllib.request.Request('http://localhost:8000/api/batches/process',
              data=json.dumps({'seed': 42, 'rows': 100}).encode(),
              headers={'Content-Type': 'application/json'}, method='POST')
          r = urllib.request.urlopen(req, timeout=30)
          assert r.status == 200, 'Batch processing failed'
          batch = json.loads(r.read())

          # 4. Verify cases exist
          r = urllib.request.urlopen('http://localhost:8000/api/cases')
          cases = json.loads(r.read())
          assert len(cases) > 0, 'No cases generated'

          # 5. Verify metrics endpoint returns data
          r = urllib.request.urlopen('http://localhost:8000/api/metrics')
          metrics = json.loads(r.read())
          assert 'match_rate' in metrics or 'throughput' in metrics, 'Metrics missing expected fields'

          print(f'Smoke test passed: {len(cases)} cases, metrics OK')
          "
```

**CI does NOT require**: Ollama, any LLM model (tests mock the adapter), paid services.

---

## P. Four-Chunk Implementation Roadmap

> [!IMPORTANT]
> **Contingency buffer**: Do not assume every one of the 56 hours is productive feature-building. Reserve ~8 hours as unallocated recovery capacity across the four chunks. Internally plan: **48 hours build + 8 hours contingency**. Each chunk nominally allocates ~12h of committed feature work + ~2h of buffer for dependency conflicts, rendering quirks, schema issues, integration surprises, and demo polish. The buffer does not need its own commit.

### Chunk 1: Foundation + Data Model + Scenario Library + Deterministic Baseline
**~12h build + ~2h buffer | Commit: `feat(foundation): data model, scenario library, synthetic generator, deterministic baseline`**

| Task | Hours | Exit Condition |
|---|---|---|
| Repository scaffold: FastAPI + Next.js shell + Makefile | 2h | `make dev` starts both servers |
| Domain models (Pydantic v2): all objects including InventoryMove, four-level EventStatus | 2h | All models validate; unit tests pass |
| DuckDB 1.4.5 LTS persistence layer | 2h | Round-trip read/write for all domain objects |
| Economic Event Scenario Library (12 scenarios) | 2h | Each scenario defined with observed data + ground truth |
| Synthetic data generator from scenario library | 2h | `generate_dataset.py --rows 10000 --seed 42` works |
| CSV ingestion + normalization (dates, amounts, signs, inventory valuation) | 2h | Malformed rows rejected; valid rows normalized |
| Deterministic reconciliation + baseline metrics | 2h | Clean cases reconcile; baseline frozen |

**At end of Chunk 1:**
- Project runs from clean checkout
- 10,000-record synthetic dataset from scenario library with ground truth
- Deterministic baseline metrics available
- Tests pass

---

### Chunk 2: Value-Flow Engine + Latent Events + Shadow Ledger + Pattern Engine
**~12h build + ~2h buffer | Commit: `feat(engine): value-flow graph, latent-event hypotheses, shadow ledger, pattern engine`**

| Task | Hours | Exit Condition |
|---|---|---|
| Case-local value-flow graph (NetworkX) | 2.5h | Graph builds from relevant observations per case |
| Exception miner: residuals, orphans, duplicates, timing gaps | 2h | Anomaly cases identified from residuals |
| Latent-event hypothesis engine (7+ types incl. OFF_LEDGER_DEVIATION) | 4h | Each type generates valid candidates on fixtures |
| Evidence scoring (separate from risk) + confidence calibration | 2h | Score function produces consistent rankings |
| Decision risk gate (4 independent dimensions) | 1h | OFF_LEDGER never auto-resolves; materiality gate works |
| Shadow Ledger: append-only inferred-event store + audit trail | 1h | Every inference persisted with provenance |
| Cross-case pattern engine (P0) | 1.5h | Pattern clusters detected from seeded scenarios |

**At end of Chunk 2:**
- Full engine pipeline operational
- Shadow Ledger entries with four-level taxonomy
- Pattern engine detects recurring patterns / likely common causes
- API serves all case/batch/metrics endpoints
- Tests pass, improvement over baseline measurable

---

### Chunk 3: Frontend + Graph Visualization + Evaluation Harness
**~12h build + ~2h buffer | Commit: `feat(app): web console, case workspace, graph visualization, evaluation harness`**

| Task | Hours | Exit Condition |
|---|---|---|
| Command Center: batch health, metrics, pattern panel, "Process Batch" | 3h | Judge can trigger batch, see summary + patterns |
| Exception Queue: prioritized case list, filters, status colors | 2h | Cases sortable by impact; click-through works |
| Case Workspace — Evidence tab: Official vs Shadow side-by-side | 3h | Evidence, confidence, decision visible for any case |
| Case Workspace — Graph tab: react-force-graph-2d, observed vs inferred nodes | 3h | Interactive graph renders; wow moment works |
| Case Workspace — Audit tab: chronological log with provenance | 1h | Full audit trail visible per case |
| Evaluation harness: held-out benchmark + adversarial test suite | 2h | `run_benchmark.py` produces reproducible metrics |

**At end of Chunk 3:**
- Full user-facing application works end-to-end
- Judge can run batch, see metrics, investigate cases, view graphs
- Evaluation produces reproducible held-out metrics
- UI is polished, dark-mode, data-dense
- Tests pass

---

### Chunk 4: Hardening + Adversarial QA + Demo + Documentation
**~12h build + ~2h buffer | Commit: `feat(release): hardening, adversarial QA, CI/CD, demo preparation, documentation`**

| Task | Hours | Exit Condition |
|---|---|---|
| Adversarial QA: ≥25 deceptive cases, false-positive guardrails | 3h | Engine refuses to auto-resolve adversarial cases |
| Failure testing: LLM disabled, malformed input, conflicting evidence | 2h | App handles all failure modes gracefully |
| LLM adapter (P1, if time): Ollama/Qwen3 for case explanations | 2h | Optional layer adds narrative; degrades gracefully |
| Demo seed: three hero scenarios (kirana, ride-hailing, pattern collapse) | 2h | `seed_demo.py` creates compelling demo batch |
| GitHub CI/CD finalization | 1h | All workflows pass |
| README: problem, architecture, setup, benchmark, screenshots | 2h | New contributor can set up from README |
| Architecture diagram + demo script + metrics freeze | 1h | Matches implemented code; headline numbers reproducible |
| Final polish: screenshot capture, edge case fixes | 1h | Ready for 5-minute video recording |

**At end of Chunk 4:**
- Everything green: tests, CI, benchmark, adversarial suite
- Three hero demo scenarios work reliably
- README complete and accurate
- Metrics frozen and reproducible from one command
- Ready for 5-minute video

---

## Q. Prerequisites

### Developer Machine

| Prerequisite | Version | Why |
|---|---|---|
| Python | 3.12+ | Backend runtime |
| Node.js | **20.9+** (maintained LTS) | Next.js 16 requirement |
| npm | 10+ | Package management |
| Git | 2.40+ | Version control |
| Ollama | 0.33+ | **Optional** — P1 LLM runtime |

### First-Time Setup

```bash
git clone <repo-url> && cd shadowledger
python -m venv .venv && source .venv/bin/activate
pip install -e "./apps/api[dev]"
cd apps/web && npm install && cd ../..
python scripts/generate_dataset.py --rows 10000 --seed 42
make dev    # starts FastAPI + Next.js concurrently
```

### Hardware

| Component | Minimum | Recommended |
|---|---|---|
| RAM | 8 GB (no LLM) | 16 GB (with Qwen3 8B) |
| CPU | 4 cores | 8 cores |
| Storage | 2 GB free | 10 GB free |

---

## R. Risks and Fallback Plans

| Risk | Signal | Kill-Switch |
|---|---|---|
| **LLM too slow** | Explanation > 10s | LLM is P1; deterministic engine is P0. Disable adapter. |
| **Graph UI time sink** | react-force-graph blocks engine | Ship static evidence diagram; add interactive graph after P0 |
| **Hypothesis space explodes** | Combinatorial search | Cap at 9 types; candidates only around residual clusters |
| **Metrics look weak** | Precision < 95% | Raise review threshold; reduce auto-resolve scope. Report coverage trade-off honestly. |
| **Synthetic data too artificial** | Judge calls it toy | Add realistic noise, timing shifts, contradictions |
| **Frontend falls behind** | Hour 40, UI incomplete | Nuclear fallback: Streamlit single-page (last resort) |
| **Ollama fails on demo machine** | Model won't load | P1 feature; deterministic engine unaffected |
| **Pattern engine too complex** | Clustering takes too long | Simplify to structural signature grouping (no ML clustering) |
| **DuckDB corruption** | Database file corrupted | Regenerate from seed; data is reproducible |

---

## S. Definition of Done

| # | Criterion |
|---|---|
| 1 | Clean machine can clone, install, run without paid APIs |
| 2 | 10,000-record synthetic batch processes end-to-end |
| 3 | Deterministic baseline matches with transparent reason codes |
| 4 | Case-local value-flow graph built for investigated cases |
| 5 | ≥6 hypothesis types including OFF_LEDGER_DEVIATION, unit-tested |
| 6 | Four-level event taxonomy: OBSERVED / DERIVED / INFERRED_LATENT / UNOBSERVED_DEVIATION |
| 7 | Evidence confidence separated from decision risk |
| 8 | Three explicit outcomes: AUTO_RESOLVE, HUMAN_REVIEW, UNRESOLVED |
| 9 | OFF_LEDGER_DEVIATION can NEVER auto-resolve |
| 10 | Cross-case pattern engine detects recurring patterns / likely common causes (P0) |
| 11 | Held-out benchmark reproducible from one command |
| 12 | Web UI: Command Center + Case Workspace + Exception Queue |
| 13 | LLM is optional; app works with adapter disabled |
| 14 | GitHub Actions passes backend tests, type checks, frontend build, smoke test |
| 15 | 5-minute demo reproduces headline results from clean dataset |
| **16** | **Every headline demo metric is generated automatically by the reproducible evaluation pipeline (`run_benchmark.py`); no number shown in the pitch may be manually typed or hard-coded** |

---

## T. Final Demo Flow

### 5-Minute Pitch Narrative

| Time | Story | Screen |
|---|---|---|
| 0:00–0:30 | "A ledger tells you what was recorded. ShadowLedger investigates what the records imply actually happened." | Problem statement |
| 0:30–1:10 | Show ₹100→₹98+chocolate AND ₹150 ride→possible ₹200 deviation. Introduce Official vs Shadow concept. | Animated diagram |
| 1:10–2:50 | Run 10K batch. Command Center shows real metrics (not invented numbers). Click "Show me what the ledger cannot explain." Open kirana case: Official vs Shadow side-by-side. Animate value-flow graph. | Command Center → Case Workspace |
| 2:50–3:40 | **Hero B**: Ride-hailing case. Show three evidence situations: digital trace found (REVIEW), cash-only (UNRESOLVED), repeated pattern detected. Then **Hero C**: 400+ tiny anomalies → 3 recurring patterns. | Case Workspace → Pattern panel |
| 3:40–4:20 | Show deliberate failure: conflicting evidence → "We don't know." Show adversarial case the system refused to auto-resolve. | Case Workspace with adversarial case |
| 4:20–5:00 | Metrics: precision at coverage, unsafe auto-resolutions (target: 0), value explained. Architecture: "AI is used only where it adds value." Close: **"We optimized for safe automation, not maximum automation."** | Metrics + Architecture |

---

## U. Recommended Directory Structure

```
shadowledger/
├── apps/
│   ├── web/                              # Next.js 16 + TypeScript
│   │   ├── app/                          # App Router pages
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx                  # Command Center
│   │   │   ├── exceptions/
│   │   │   │   └── page.tsx              # Exception Queue
│   │   │   └── cases/
│   │   │       └── [id]/page.tsx         # Case Workspace (tabs: evidence, graph, audit)
│   │   ├── components/
│   │   │   ├── ui/                       # shadcn/ui primitives
│   │   │   ├── dashboard/               # Command Center components
│   │   │   ├── cases/                   # Case Workspace components
│   │   │   ├── graph/                   # Value-flow graph
│   │   │   └── layout/                  # Shell, nav, theme
│   │   ├── lib/
│   │   │   ├── api.ts                   # API client
│   │   │   └── utils.ts
│   │   ├── styles/globals.css
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── eslint.config.mjs            # ESLint flat config (not next lint)
│   │   └── next.config.ts
│   │
│   └── api/                              # FastAPI backend
│       ├── app/
│       │   ├── main.py
│       │   ├── api/
│       │   │   ├── routes/
│       │   │   │   ├── health.py
│       │   │   │   ├── batches.py
│       │   │   │   ├── cases.py
│       │   │   │   └── metrics.py
│       │   │   └── schemas/
│       │   ├── domain/
│       │   │   ├── models.py             # All domain objects
│       │   │   ├── enums.py
│       │   │   └── scenarios.py          # Economic Event Scenario Library
│       │   ├── engine/
│       │   │   ├── normalizer.py
│       │   │   ├── reconciler.py
│       │   │   ├── graph_builder.py      # case-local graph
│       │   │   ├── hypothesis_engine.py
│       │   │   ├── hypotheses/
│       │   │   │   ├── refund.py
│       │   │   │   ├── fee_adjustment.py
│       │   │   │   ├── inventory_settlement.py
│       │   │   │   ├── store_credit.py
│       │   │   │   ├── duplicate_reversal.py
│       │   │   │   ├── timing_offset.py
│       │   │   │   ├── missing_payment.py
│       │   │   │   └── off_ledger_deviation.py  # NEW
│       │   │   ├── scorer.py             # evidence scoring (no financial risk)
│       │   │   ├── decision_gate.py      # 4-dimensional risk gate
│       │   │   └── pattern_engine.py     # cross-case patterns (P0)
│       │   ├── llm/
│       │   │   ├── adapter.py
│       │   │   ├── ollama.py
│       │   │   └── mock.py
│       │   ├── data/
│       │   │   ├── ingest.py
│       │   │   └── normalize.py
│       │   ├── persistence/
│       │   │   ├── database.py
│       │   │   ├── observation_repo.py
│       │   │   ├── event_repo.py
│       │   │   ├── case_repo.py
│       │   │   └── audit_repo.py
│       │   └── metrics/
│       │       ├── evaluator.py
│       │       └── reporter.py
│       ├── tests/
│       │   ├── conftest.py
│       │   ├── test_models.py
│       │   ├── test_normalizer.py
│       │   ├── test_reconciler.py
│       │   ├── test_graph.py
│       │   ├── test_hypotheses.py
│       │   ├── test_off_ledger.py        # OFF_LEDGER never auto-resolves
│       │   ├── test_scorer.py
│       │   ├── test_decision_gate.py
│       │   ├── test_pattern_engine.py
│       │   ├── test_api.py
│       │   └── test_adversarial.py
│       └── pyproject.toml
│
├── data/
│   ├── generated/
│   ├── truth/                            # .gitignored
│   └── schemas/
│
├── scripts/
│   ├── generate_dataset.py               # generates from scenario library
│   ├── run_benchmark.py                  # evaluation harness
│   └── seed_demo.py                      # three hero scenarios
│
├── docs/
│   ├── architecture.md
│   ├── evaluation.md
│   ├── scenarios.md                      # scenario library documentation
│   └── demo-script.md
│
├── .github/workflows/ci.yml
├── Makefile
├── README.md
├── LICENSE
└── .gitignore
```

---

## Architecture Decisions — Final Status

| # | Decision | Status | Notes |
|---|---|---|---|
| 1 | Next.js 16 over Streamlit | ✅ APPROVED | Professional finance-console; Streamlit as nuclear fallback only |
| 2 | Qwen3 8B local LLM | ✅ APPROVED | **P1 optional**; deterministic core must work without it |
| 3 | Four-commit structure | ✅ APPROVED | Simplified workflow: chunk work → squash → commit → push |
| 4 | DuckDB sole data store | ✅ APPROVED | **LTS 1.4.5** for stability |
| 5 | NetworkX for graphs | ✅ APPROVED | **Case-local** graphs only, not giant global graph |
| 6 | Cross-case pattern engine | ✅ **PROMOTED TO P0** | Core differentiator, required for demo |
| 7 | No Docker for primary demo | ✅ APPROVED | Native demo; Docker as optional backup |
| 8 | Tailwind CSS v4 | ✅ APPROVED | With ESLint CLI (not next lint) for linting |
