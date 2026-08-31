# ShadowLedger — Track 04 Technical Build Guide

**Track:** AI Finance Controller  
**Core product:** Value-Flow Reconstruction Engine / Shadow Ledger  
**Build constraint:** 56 focused hours, ₹0 recurring spend, open/free stack  
**Primary interface:** Desktop-first local web app

## 1. Locked product decision

ShadowLedger is a local-first web application that keeps the official ledger immutable, reconstructs economic events across multiple source records, builds an uncertainty-aware Shadow Ledger, and routes cases through an explicit confidence gate. The LLM is a semantic helper, never the financial authority.

## 2. Stack at a glance

| Layer | Choice |
|---|---|
| Frontend | Next.js + TypeScript |
| UI | Tailwind CSS + shadcn/ui |
| Graph UI | @xyflow/react |
| Backend | FastAPI |
| Validation | Pydantic v2 |
| Analytics | DuckDB + Parquet/CSV |
| Transformations | Polars |
| Graph core | Custom adjacency + NetworkX where useful |
| Matching | RapidFuzz + deterministic scoring |
| Metrics | scikit-learn / scipy |
| LLM runtime | Ollama |
| Runtime model | Qwen3 8B; Qwen3 4B fallback |
| Coding agent | OpenCode; Aider fallback |
| Testing | pytest + Vitest/Playwright smoke |
| CI | GitHub Actions |
| Packaging | Docker Compose optional |

## 3. Architecture

```text
CSV/Parquet/JSON
      ↓
Ingestion + Normalization
      ↓
Deterministic Reconciliation
      ↓
Economic Event Graph
      ↓
Exception Miner
      ↓
Latent-Event Engine
      ↓
Shadow Ledger
      ↓
Confidence Gate ──→ Auto-resolve / Human review / Unresolved
      ↓
Audit + Metrics
      ↓
Next.js Analyst Console
```

## 4. Core features

1. Batch ingestion and schema validation
2. Deterministic matching baseline
3. Value-flow graph
4. Latent-event hypotheses: refund, fee/adjustment, partial settlement, inventory settlement, customer credit, duplicate/reversal, timing lag, unknown
5. Shadow Ledger
6. Confidence gate
7. Immutable audit trail
8. Root-cause/pattern clustering
9. Micro-leakage aggregation
10. Held-out evaluation
11. Web command center, queue, case view, graph, audit view
12. Optional grounded LLM explanations

## 5. LLM rule

**Allowed:** semantic normalization, constrained classification, grounded narrative.  
**Not allowed:** arithmetic, matching, thresholds, final confidence, final financial decision.

## 6. Git strategy

`main` is demo-safe. Use `feat/*` and `fix/*`. Small atomic commits. CI must be green before merge. Tag milestones. Never commit model files, `.env`, secrets, huge generated datasets or private keys.

## 7. CI outline

Backend: Ruff → mypy → pytest. Frontend: lint → typecheck → build. Integration: generate small fixture → run engine → assert metrics.

## 8. 56-hour roadmap

0–3 scaffold; 3–8 dataset; 8–14 ingestion; 14–20 baseline; 20–28 graph; 28–36 latent events; 36–40 shadow ledger/gate; 40–45 UI; 45–49 case view; 49–52 evaluation; 52–54 polish; 54–56 demo freeze.

## 9. Definition of Done

The app runs locally without paid APIs, processes a 10k synthetic batch, reports throughput/precision/recall/exceptions, constructs a value-flow graph, reconstructs at least five event types, separates official from inferred truth, logs evidence/confidence/decision, provides the core UI, passes CI, and reproduces the pitch from a clean checkout.

## 10. Coding-agent prompts

Use the master context prompt plus staged prompts: scaffold → data model → deterministic matcher → graph → latent-event engine → confidence/audit → UI → LLM adapter → adversarial QA. Never ask for the whole project in one prompt.


## Current sources

- Razorpay Buildathon: https://razorpay.com/buildathon/
- Qwen3-8B: https://huggingface.co/Qwen/Qwen3-8B
- Qwen3 via Ollama: https://ollama.com/library/qwen3
- Next.js: https://nextjs.org/docs
- FastAPI: https://fastapi.tiangolo.com/
- DuckDB: https://duckdb.org/docs/current/
- NetworkX: https://networkx.org/documentation/stable/
- OpenCode: https://github.com/sst/opencode
- Aider: https://github.com/Aider-AI/aider
