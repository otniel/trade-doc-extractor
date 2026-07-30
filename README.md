# Trade Document Extractor

Self-validating extraction pipeline for trade confirmations. Pulls typed fields
out of a trade-confirmation PDF, and catches the errors an LLM makes *silently* —
plausible-looking values that are wrong — with a schema + business-rule
validation layer and an automated repair loop.

The centerpiece is the **eval harness**: field-level accuracy measured against a
hand-labeled golden set, so every change is judged by a number, not a vibe.

## What it does

A naive "PDF → LLM → JSON" pipeline produces output that *looks* right and passes
`json.loads`, but contains silent field errors. Concrete example from the sample
doc: the model reads `Unit: USD per barrel` (a **price** unit) into the
**quantity** unit field. The math still checks out, so nothing complains — and
the extraction is wrong.

This pipeline makes that failure loud: `price.per_unit` and `quantity.unit` are
separate typed fields, and a business rule requires them to agree. On any
violation the graph re-prompts the model with the specific error and its own
prior output, up to a retry budget.

## Architecture

```
PDF ──> text (PyMuPDF) ──> LLM extract ──> validate ──┬─ ok ────────> typed JSON
                                             ^         │
                                             │         └─ errors ──> repair (LLM)
                                             └───────────────────────────┘
                                                   (LangGraph, capped retries)
```

- **Extraction:** PyMuPDF text → LLM with a schema-constrained prompt
- **Validation:** Pydantic types + cross-field business rules (unit/currency
  coherence, notional = price × quantity, date ordering, delivery rules)
- **Repair:** LangGraph loop — one conditional edge routes failures back through
  a targeted correction prompt; unresolved after the budget returns a traced miss
- **Measurement:** eval harness scoring field-level accuracy vs a golden set

## Quick start

```bash
uv sync                 # or: pip install -r requirements-dev.txt
cp .env.example .env     # add your ANTHROPIC_API_KEY
make test                # 21 offline tests, no API calls

make run FILE=documents/trade_confirmation_001.pdf   # extract one doc
make eval                                            # accuracy vs golden set
```

Docker:

```bash
docker build -t trade-doc-extractor .
docker run --rm -e ANTHROPIC_API_KEY=sk-ant-... trade-doc-extractor
```

## Scope

This ship is a **thin vertical slice**: one document type (trade confirmation),
end to end, with the validation/repair loop and the eval harness. Multi-document
support and retrieval are on the roadmap, not in this cut — see below.

## Results

Field-level accuracy is measured by the eval harness against the golden set.
Baseline is recorded with the repair loop **disabled** (`--max-repairs 0`), then
re-measured with it on, so the improvement is real and not self-graded. Numbers
are published here once measured — none before.

## Corpus

`documents/` holds a trade confirmation (the current extraction target) plus
invoices, purchase orders, statements, contracts, and off-domain SEC filings.
In this slice only the trade confirmation is scored; the rest seed the roadmap
(future document types) and serve as "should not produce a valid
TradeConfirmation" robustness cases.

## Roadmap (post-ship)

- Additional document types (invoice, PO, statement, contract) with per-type
  schemas and goldens
- Retrieval: Postgres + pgvector, source-cited Q&A over the extracted corpus
- Observability + a retrieval eval
- Table-aware extraction (pdfplumber) for messy real-world templates

## Stack

Python · PyMuPDF · Pydantic · LangGraph · Anthropic API · pytest · Docker
