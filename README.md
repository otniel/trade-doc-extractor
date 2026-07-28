# Trade Document Extractor

Structured extraction + RAG pipeline for financial and trade documents.
Pulls typed fields out of trade confirmations, invoices, POs, and statements,
validates them against a schema with an automated repair loop, and makes the
corpus queryable with source-cited retrieval.

The centerpiece is the **eval harness**: field-level accuracy measured against a
hand-labeled golden set, so every change to the pipeline is judged by a number,
not a vibe.

## Quick Start

```bash
docker-compose build
docker-compose up
```

## Architecture

```
PDF → Text Extraction → LLM Structured Extraction → Validation + Repair → Postgres/pgvector → Cited Retrieval
```

- **Extraction:** PyMuPDF for text (pdfplumber for tables)
- **Structuring:** LLM with schema-constrained output, Pydantic models
- **Validation:** LangGraph loop — schema + semantic checks with an LLM repair pass
- **Persistence & retrieval:** Postgres + pgvector, retrieval with source citations
- **Measurement:** eval harness scoring field-level accuracy vs a golden set

## Results

Accuracy and cost are measured by the eval harness against a hand-labeled golden
set. Baseline is recorded when the harness lands (Day 4); final numbers are
posted at ship.

_Goal: raise field-level accuracy and cut per-document cost via the
validation/repair loop. Measured numbers replace this section once the harness
runs — no numbers are published before they're measured._

## Corpus

12 documents spanning three difficulty tiers:

- **Clean, self-authored** (ground truth): trade confirmation, invoice, purchase
  order, statement, contract.
- **Messy real-world templates**: UNICEF PO, UW invoice, Harvest invoice.
- **Off-domain** (SEC 8-K / 10-K filings): used as "correctly reject /
  low-confidence" cases, not extraction targets.

## Roadmap

| Day | Milestone | Status |
|-----|-----------|--------|
| 1 | Scaffold, schema, Docker, corpus | ✅ |
| 2 | PDF → text → LLM → structured JSON (happy path) | ✅ |
| 3 | Validation + repair loop (LangGraph) | ◻ |
| 4 | Eval harness + baseline | ◻ |
| 5 | Postgres + pgvector persistence | ◻ |
| 6 | Retrieval with source citations | ◻ |
| 7 | Observability + retrieval eval | ◻ |
| 8 | Hardening | ◻ |
| 9 | Demo + writeup | ◻ |
| 10 | Ship | ◻ |

## Stack

Python · PyMuPDF · LangGraph · Pydantic · Postgres + pgvector · Docker · Anthropic API
