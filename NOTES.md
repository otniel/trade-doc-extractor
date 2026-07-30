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
| D4 | Eval harness + **record baseline** | next |
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

---

## Open items / findings

- **Schema vs. real doc gap (found D4 prep).** The sample doc names one
  *counterparty* (Shell Energy Trading SARL) + two individual signatories, and
  no explicit BUY/SELL side. But the schema requires `buyer`, `seller`, and
  `side`. These three fields can't be reliably ground-truthed from the doc, so
  the eval golden omits them from scoring. **Decision needed before D4 is
  trustworthy:** either replace buyer/seller with a single `counterparty` and
  make `side` optional (fits the doc), or add docs where buyer/seller/side are
  explicit. Leaning toward the schema change.
- **Golden set is n=1.** One scored doc is a weak accuracy signal. Add 2–3 more
  trade-confirmation docs (one clean, one messy) before publishing a number.
- **String fields are exact-match** in the scorer (commodity, delivery_location).
  Free-text near-misses count as wrong; fine for v1, note it.

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
