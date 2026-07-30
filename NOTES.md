# NOTES.md — trade-doc-extractor

Working log + decisions. Compressed to a thin vertical slice.
**Ship: Fri Jul 31, 2026.**

The eval harness is the centerpiece — field-level accuracy vs a hand-labeled
golden set. Everything else exists to move that number honestly.

---

## Scope decision (compression)

Narrowed from the original 10-day multi-doc + RAG build (ship Aug 7) to a single
document type shipped end to end by Jul 31: **TradeConfirmation only**, with the
validate/repair loop and the eval harness. RAG/Postgres/pgvector, multi-doc
types, and observability moved to the post-ship roadmap. Reason: the job funnel
needs a *shipped, working* artifact now; a half-built broad system ships nothing.

---

## Pitch target (a number to earn, not to claim)

> Goal: raise field-level accuracy and cut per-doc cost via the validate/repair
> loop — e.g. a jump from a no-repair baseline to a repaired score.

**Record the baseline on D4 with `--max-repairs 0` BEFORE the loop can flatter
the number.** No measured baseline = no story. Nothing goes in the README until
the harness produces it.

---

## Stack / decisions

- Python · PyMuPDF (text) · Pydantic v2 (schema + rules) · LangGraph (repair
  loop) · Anthropic SDK · pytest · Docker
- LLM: `claude-sonnet-4-6`
- Config (resolved D2): SDK reads `ANTHROPIC_API_KEY` from `.env` via
  python-dotenv, not shell export — survives across sessions. `.env` is
  gitignored; check `git status` before every commit.
- Packaging: `src/` is a package (`src/__init__.py`); run with
  `python -m src.cli <pdf>` from the repo root — intra-package imports are
  relative, tests import `from src....`, pytest uses `pythonpath=["."]`.
  pyproject is the dependency source of truth; `uv` locks/runs; requirements.txt
  is the pip fallback.

---

## Plan (compressed)

| Day | Scope | Status |
|-----|-------|--------|
| D1 | Scaffold, schema, Docker, corpus | done (Mon Jul 27) |
| D2 | PyMuPDF → text → LLM → structured JSON (happy path) | done (Tue Jul 28) |
| D3 | Validation + repair loop (LangGraph) + tests | done (Wed Jul 29) |
| D4 | Eval harness + **record baseline** | done (Wed Jul 29) |
| D5 | Ship: README/demo, final numbers, LinkedIn launch | Fri Jul 31 |

---

## Running log

### D2 — Tue Jul 28
- **Finding (the whole pitch):** on the *clean* sample doc
  (`trade_confirmation_001.pdf`, TC-2026-0471B) the model reads
  `Unit: USD per barrel` — a **price** unit — into the **quantity** unit field.
  Math still checks (1000 × 85.42 = 85,420), so the error is silent. Caught by
  D3 validation, measured by D4 eval.

### D3 — Wed Jul 29
- Typed Pydantic schema; `price.per_unit` and `quantity.unit` separated so the
  unit conflation is *checkable*. Business rules in one accumulating
  model_validator (unit/currency coherence, notional≈price×qty, date ordering,
  physical-delivery). Repair loop (LLM injected as a callable, capped retries,
  returns a traced miss instead of raising). Wired as a LangGraph graph, one
  conditional edge on the validation result. 21 offline tests green.

### D4 — Wed Jul 29 (eval harness + measured baseline)
- Expanded the golden corpus from n=1 to n=4: kept `trade_confirmation_001`
  (clean) and added 3 *adversarially designed* docs
  (`trade_confirmation_002/003/004.pdf`, generated via
  `scripts/generate_corpus_docs.py`), each engineered to reproduce a specific
  silent-error class -- an invalid-unit decoy (`kWh`) sitting next to the
  quantity (002), the exact D2 unit-conflation layout: bare quantity number +
  weight decoy, then a `Unit:` line that's actually the price's unit (003), and
  a decoy EUR figure sitting beside the USD notional (004).
- **Measured, live, `claude-sonnet-4-6`:**

  ```
  --max-repairs 0            --max-repairs 2
  59/61 fields = 96.7%       59/61 fields = 96.7%
  resolved 4/4, 0 repairs    resolved 4/4, 0 repairs
  ```

  Identical. **The repair loop fired zero times, on any of the 4 docs,
  including the 3 built specifically to trip it.**
- **Finding (supersedes the D2/D3 open question):** this is now the *second*
  time this happened -- D3's clean doc, and now D4's adversarial corpus. On
  `claude-sonnet-4-6`, the D2 unit-conflation bug does not reproduce reliably
  even when the layout is deliberately engineered to invite it. The two misses
  that do exist are both free-text exact-match scorer artifacts, not
  extraction errors, and neither violates a business rule so neither is
  repair-loop-catchable in principle: `trade_confirmation_001.delivery_location`
  (`"Rotterdam (ARA)"` vs `"Rotterdam"`) and
  `trade_confirmation_002.commodity` (model dropped the `"(Financial Swap)"`
  parenthetical).
- **Decision (per the D2 contingency plan): reframe the pitch.** Not "accuracy
  jump via repair" -- that's false on this evidence, full stop. Instead: *a
  validated reliability net*. The business-rule validator is a hard
  architectural guarantee -- proven deterministically by the scripted-LLM
  tests (`test_schema.py`, `test_extract.py`, `test_graph.py`), independent of
  whether any given model trips it on any given run. The honest claim: for a
  financial document, a silently wrong unit is real money; this pipeline makes
  that failure structurally impossible to ship silently, regardless of
  whether *this* corpus, on *this* model, happened to produce one today.
- No repair-delta number goes in the README. There isn't one. The README gets
  the 96.7%/4-doc number plus this finding, stated as a finding, not
  papered over.

---

## Open items / findings

- **Schema vs. real doc gap — RESOLVED.** The sample doc names one
  *counterparty* (Shell Energy Trading SARL) + two individual signatories, and
  no explicit BUY/SELL side; the schema required `buyer`, `seller`, `side`, so
  the model was forced to guess -- e.g. reading signatory "Robert Zhang" (a
  person) into `buyer`. **Decision (revised from the original lean):** did
  *not* collapse buyer/seller to a single `counterparty` field. That plan
  predated the D4 corpus expansion; now that 3 of 4 docs (002/003/004) state a
  real, distinct buyer *and* seller *and* side, collapsing to one field would
  have discarded real information the corpus mostly does have, just to fit the
  one doc that doesn't. Instead: `buyer`, `seller`, `side` are now
  `Optional[...] = None` in `src/schema.py`. Docs that state them get them
  populated and scored (002/003/004); doc 001 correctly gets `None` instead of
  a fabricated guess. Also updated the extraction prompt (`_SCHEMA_HINT` in
  `src/extract.py`) to mark these `?`-optional and explicitly instruct the
  model not to infer a buyer/seller/side from signatory names when the
  document doesn't clearly state them -- the schema alone doesn't stop
  fabrication if the prompt still implies the fields are mandatory. Two new
  tests (`test_buyer_seller_side_optional`,
  `test_buyer_seller_side_populated_when_present`) cover both paths.
- **Golden set is n=1.** ~~One scored doc is a weak accuracy signal.~~ **Resolved
  D4:** now n=4 (`trade_confirmation_001` clean + `002/003/004` adversarial).
  New docs 002/003/004 all state buyer/seller/side explicitly, so those fields
  *are* scored there -- the ambiguity gap above is specific to doc 001, not
  structural to the corpus.
- **String fields are exact-match** in the scorer (commodity, delivery_location).
  Confirmed twice now: doc 001's `delivery_location` (`"Rotterdam (ARA)"` vs
  `"Rotterdam"`) and doc 002's `commodity` (dropped the `"(Financial Swap)"`
  parenthetical). Both free-text near-misses, not extraction errors. Fine for
  v1 with 2 known instances noted; fix (fuzzy/canonicalized string scoring) is
  the last item before D5 if time allows.

---

## Lessons (engineering-judgment log — keep for the writeup)

- **Registry beats secondhand claims.** `pip index versions <pkg>` queries PyPI
  directly — the source of truth for what a clean machine can install. Overrules
  web searches, docs, and memory.
- **`--dry-run` / "already satisfied" proves nothing** about a clean fetch — it
  found the local copy. Force a real index check.
- **`requirements.txt` = direct deps only**; let the resolver handle transitives.
- **Measure before you improve.** Record the no-repair baseline before turning on
  the repair loop, or the improvement is unfalsifiable.

---

## Launch post (parked — post WITH the repo, not before)

Angle: "AI Engineer" in most listings = reliable backend systems around LLMs, not
ML research. Let the build be the argument.
