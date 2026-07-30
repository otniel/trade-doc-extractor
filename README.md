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
make test                # 25 offline tests, no API calls

make demo                                            # 2 min, no API key needed --
                                                      # scripted repair-loop walkthrough
make run FILE=documents/trade_confirmation_001.pdf   # extract one doc (live API)
make eval                                            # accuracy vs golden set (live API)
```

`make demo` is the fastest way to see the point of this project: it runs the
real validate/repair loop end to end with a scripted LLM response that
reproduces the exact silent unit-conflation bug, then repairs it. No API key,
no network, ~5 seconds.

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
claim one. The two field misses in this run were both the same failure mode:
a free-text exact-match scorer rejecting a trailing parenthetical annotation
(`"Rotterdam (ARA)"` vs `"Rotterdam"`, `"X (Financial Swap)"` vs `"X"`) —
not extraction errors, and neither trips a business rule. The scorer has
since been fixed to allow that one narrow case (see `eval/run_eval.py::_eq`);
the table above predates that fix and hasn't been re-measured, so it's kept
as originally recorded rather than replaced with an unverified number.

The honest claim this project makes instead: the validation layer is a
correctness guarantee, not a measured accuracy bump. `test_schema.py`,
`test_extract.py`, and `test_graph.py` prove deterministically — via a scripted
fake LLM, no live-model luck involved — that a unit/currency/notional
mismatch is caught and repaired every time it occurs (`make demo` shows this
directly). For a financial document, a silently wrong unit is real money;
this pipeline makes that failure structurally impossible to ship silently,
independent of whether any particular model, on any particular run, happens
to produce one.

## Known limitations

- **Repair loop is unexercised in live measurement.** 0/61 fields needed a
  repair across the current corpus/model combination. Its correctness is
  proven by deterministic scripted-LLM tests, not by a live-model accuracy
  delta — see Results above.
- **Golden corpus is small (n=4).** Enough to prove the pipeline works
  end-to-end and to build adversarial cases against, not enough to make a
  strong statistical accuracy claim.
- **Free-text fields are near-exact-match.** `commodity` and
  `delivery_location` allow only a trailing `(...)` annotation to differ;
  any other paraphrase is scored wrong even if semantically equivalent.
- **`buyer`/`seller`/`side` are optional by design**, populated only when a
  document unambiguously states them (see NOTES.md D4) — a doc that names one
  counterparty and no explicit side will correctly return `null`, not a guess.
- **Single document type.** See Scope and Roadmap below.

## Corpus

`documents/` holds 4 trade confirmations (the current extraction target,
scored against `eval/golden/`) plus invoices, purchase orders, statements,
contracts, and off-domain SEC filings. `trade_confirmation_001.pdf` is a clean
real-world-style sample; `002/003/004` are synthetic docs generated via
`scripts/generate_corpus_docs.py`, each engineered to invite a specific silent
extraction error (see Results). The non-trade-confirmation documents aren't
scored in this slice; they seed the roadmap (future document types) and serve
as "should not produce a valid TradeConfirmation" robustness cases.

## Roadmap (post-ship)

- Additional document types (invoice, PO, statement, contract) with per-type
  schemas and goldens
- Retrieval: Postgres + pgvector, source-cited Q&A over the extracted corpus
- Observability + a retrieval eval
- Table-aware extraction (pdfplumber) for messy real-world templates

## Stack

Python · PyMuPDF · Pydantic · LangGraph · Anthropic API · pytest · Docker

## License

MIT — see [LICENSE](LICENSE).
