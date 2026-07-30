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

Measured live against a 4-doc golden set (`claude-sonnet-4-6`): 1 clean sample
doc plus 3 documents built specifically to invite the unit-conflation bug,
an invalid-unit decoy, and a currency decoy.

| `--max-repairs` | field-level accuracy | resolved | repairs fired |
|---|---|---|---|
| 0 | 59/61 = 96.7% | 4/4 | 0 |
| 2 | 59/61 = 96.7% | 4/4 | 0 |

Identical. The repair loop did not fire once, even on the documents engineered
to trip it — so there is no accuracy delta to claim, and this README won't
claim one. The two field misses that do exist are free-text exact-match scorer
artifacts (e.g. `"Rotterdam (ARA)"` vs `"Rotterdam"`), not extraction errors,
and neither trips a business rule.

The honest claim this project makes instead: the validation layer is a
correctness guarantee, not a measured accuracy bump. `test_schema.py`,
`test_extract.py`, and `test_graph.py` prove deterministically — via a scripted
fake LLM, no live-model luck involved — that a unit/currency/notional
mismatch is caught and repaired every time it occurs. For a financial
document, a silently wrong unit is real money; this pipeline makes that
failure structurally impossible to ship silently, independent of whether any
particular model, on any particular run, happens to produce one.

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
