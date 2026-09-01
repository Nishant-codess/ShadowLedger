# Operator & User Manual

**Product:** ShadowLedger Value-Flow Investigation Workbench  
**Audience:** Financial Controllers, Reconciliation Analysts, Fraud Investigators, Operations Leads  
**Version:** 1.0.0  

---

## 1. Quick Tour & Navigation Overview

The ShadowLedger frontend is organized into 5 primary operational views accessible from the top navigation header:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  [✦ ShadowLedger]   [Command Center]   [Exceptions]   [Patterns]   [Benchmark]  [Docs] │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

1. **Command Center (`/`):** High-level overview of batch ingestion, macro metrics (Total Volume, Explained Volume, Residual at Risk), and interactive Quick-Launch Demo Buttons for the 3 Hero Scenarios.
2. **Exceptions Workbench (`/exceptions`):** Filterable, ranked queue of all active discrepancy cases with priority badges, confidence tiers, and quick actions.
3. **Investigation Dossier (`/cases/{case_id}`):** Deep-dive case analysis featuring interactive Value-Flow Graphs, candidate hypothesis comparisons, 7D evidence radar/progress meters, and local AI synthesis.
4. **Fleet Patterns (`/patterns`):** Structural pattern clusters grouping thousands of recurring micro-discrepancies into single systemic causes.
5. **Benchmark & Invariants (`/benchmark`):** Dynamic ground-truth performance breakdown across all 12 economic scenarios with auditable architectural invariant proofs.

---

## 2. Step-by-Step Operator Workflow

### Step 1: Processing a Batch
1. Navigate to the **Command Center (`/`)**.
2. Click **"Process Batch"** or trigger one of the Quick Hero Demos:
   - **Hero A:** Kirana Non-Monetary Settlement (Candy Change)
   - **Hero B:** Mobility Fare Deviation (Safety Refusal)
   - **Hero C:** Fleet Pattern Discovery (3 Clusters)
3. The dashboard updates immediately with baseline vs. ShadowLedger metrics.

---

### Step 2: Investigating an Exception Case
1. Navigate to **Exceptions Workbench (`/exceptions`)**.
2. Click on any case card (e.g. `case_507805805fff`) to open the **Investigation Dossier**.
3. **Inspect the Value-Flow Graph:**
   - Visual nodes show the origin of funds (Customer, Merchant, POS, Bank, Inventory).
   - Solid arrows denote confirmed observed transactions.
   - Dashed/highlighted nodes denote inferred latent events (e.g. MDR Fee, Chocolate Change).

---

### Step 3: Evaluating Hypotheses & Evidence
1. Scroll to the **Candidate Hypotheses** section.
2. Review the ranked explanations:
   - `Confidence Score`: Composite calibrated score ($0.00$ to $1.00$).
   - `Confidence Tier`: `DEFINITIVE` ($\ge 0.95$), `HIGH` ($\ge 0.80$), `MEDIUM` ($\ge 0.60$), `SPECULATIVE` ($< 0.60$).
3. Expand **Evidence Breakdown** to view the 7 dimension scores:
   - *Mathematical Conservation*
   - *Temporal Plausibility*
   - *Entity Linkage*
   - *Observation Coverage*
   - *Domain Rule Fit*
   - *Parsimony*
   - *Contradiction Penalty*

---

### Step 4: Taking an Operator Action
In the action toolbar at the top right of the case dossier, choose one of the following actions:
- **Accept Hypothesis:** Approves the engine's selected candidate explanation and records it into the immutable Audit Trail.
- **Escalate to Supervisor:** Flags the case for senior management review due to materiality or policy uncertainty.
- **Mark Unresolved:** Confirms that available data is insufficient to reach an economic conclusion without making unfounded assumptions.

---

## 3. Understanding Architectural Safety Invariants

| Invariant Banner | Meaning & Operator Action |
| :--- | :--- |
| **`AUTO_RESOLVED` (Green)** | Mathematical conservation closed with high confidence ($\ge 0.85$) and materiality below threshold ($< ₹5,000$). Safe to proceed. |
| **`HUMAN_REVIEW` (Yellow)** | Mandatory review required. Triggered by Level 4 `OFF_LEDGER_DEVIATION`, moderate confidence, or high financial materiality. |
| **`UNRESOLVED` (Red/Rose)** | The engine safely refused to hallucinate or guess a resolution because counterparty evidence is missing (e.g., untracked physical cash). |

---

## 4. Troubleshooting & FAQ

### Q1: Why did a case get marked `UNRESOLVED` instead of guessing a refund?
**A:** ShadowLedger enforces a zero-hallucination policy. If an exception lacks corroborating temporal, entity, or payment traces, the engine refuses to invent a latent event.

### Q2: Can `OFF_LEDGER_DEVIATION` cases ever be auto-resolved?
**A:** No. Under the immutable safety rules of ShadowLedger, off-ledger unrecorded payments can **never** auto-resolve. They strictly escalate to human review to prevent financial leakage.

### Q3: How do I run the application locally?
```bash
# Terminal 1: Start Backend API
source .venv/bin/activate
PYTHONPATH=. uvicorn app.main:app --app-dir apps/api --port 8000

# Terminal 2: Start Frontend Web UI
cd apps/web
npm run dev
# Open http://localhost:3000
```
