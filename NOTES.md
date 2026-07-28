# NOTES.md — trade-doc-extractor

Working log + decisions for the document-extraction + RAG pipeline over
financial/trade documents. Timebox: 2 weeks. Ship: **Fri Aug 7, 2026**.

The eval harness is the centerpiece — field-level accuracy vs a hand-labeled
golden set. Everything else exists to move that number.

---

## Pitch target (the number the project is built to earn)

> "71% → 94% field-level accuracy, cost/doc $0.12 → $0.07."

These are targets, not results yet. **The 71% baseline must be recorded on Day 4**
against the golden set — before the validation loop is allowed to flatter the
numbers. No baseline = no story.

---

## Stack / decisions

- Python
- PyMuPDF for text extraction (pdfplumber added later for tables)
- LangGraph for the validation/repair loop (D3)
- Structured outputs + Pydantic validation with a repair loop
- Postgres + pgvector for retrieval (D5)
- Docker
- LLM: Anthropic SDK, `claude-sonnet-4-6`

Key config resolved D2: SDK reads `ANTHROPIC_API_KEY` from env via `.env` +
`python-dotenv` (not shell export — survives across sessions). `.env` is
gitignored; verify with `git status` before every commit.

---

## Corpus (12 docs, in repo)

- **5 clean, self-made** (ground-truth easy cases): trade confirmation, invoice,
  purchase order, statement, contract.
- **Messy real templates** (the hard cases the accuracy story rests on): UNICEF PO,
  UW invoice, Harvest invoice.
- **Off-domain SEC filings** (Chevron/Exxon 8-K, JPMorgan 10-K) — used as
  "correctly reject / low-confidence" cases, not extraction targets.

---

## 10-day plan

| Day | Scope | Status |
|-----|-------|--------|
| D1  | Scope, repo scaffold, Docker builds, schema, corpus in place | ✅ done (Mon Jul 27) |
| D2  | Ingestion/parsing: PyMuPDF → text → LLM w/ schema → one happy path | ✅ done (Tue Jul 28) |
| D3  | Validation loop (LangGraph) + Pydantic validate/repair | ⏭ next |
| D4  | Eval harness + **record baseline** | — |
| D5  | Postgres + pgvector | — |
| D6  | Retrieval + citations | — |
| D7  | Observability + retrieval eval | — |
| D8  | Harden | — |
| D9  | Demo + writeup | — |
| D10 | Ship + LinkedIn launch | — |

---

## Running log

### D1 — Mon Jul 27
- Repo scaffolded, Docker builds, schema defined, corpus placed. Morning slipped
  but day closed complete.

### D2 — Tue Jul 28
- Happy path working: `extract_text()` (PyMuPDF) → `extract_fields()`
  (LLM + `model_json_schema()`) → `json.loads` → dict, on
  `trade_confirmation_001.pdf`.
- Clean doc returned **valid JSON, no markdown fences, parsed first try.** Record
  this as the "easy case works" baseline behavior — it will NOT hold on the messy
  UNICEF/UW/Harvest docs, and that gap is the whole point of the project.
- **Finding — field error on a CLEAN doc:** model returned
  `"quantity": 1000, "unit": "USD per barrel", "unit_price": 85.42`. The
  `unit` value is a *price* unit, not a *quantity* unit — quantity should be in
  barrels; USD/barrel describes the price. `total_value` math still checked out
  (1000 × 85.42 = 85,420), so the error is silent. This is concrete evidence for
  the pitch: *even clean docs produce field errors the naive pipeline doesn't
  notice.* → to be caught by D3 validation + measured by D4 eval. **Not fixed in
  D2 by design.**
- requirements.txt verified against PyPI directly (`pip index versions`), not
  guessed. All pins resolve on a clean index. Lesson logged below.

---

## Open items / parked gaps

- **D3:** semantic validation must catch the unit/quantity conflation above, not
  just schema-shape validation. A value can be schema-valid and still wrong.
- **D4:** record the 71% baseline against the golden set BEFORE the repair loop
  runs, or the improvement number is meaningless.
- **LeetCode redo slot (Thu):** redo Num Islands in-place (sink by mutating grid
  to `"0"`) from memory. First pass used a visited-set of tuples: 304ms/5%.
  In-place: 234ms/82%. Interview point: in-place marking removes the aux
  structure. Bug that cost a TLE: `grid[r][c] == "0"` (compare) vs
  `grid[r][c] = "0"` (assign).

---

## Lessons (engineering-judgment log — keep for the writeup)

- **Registry beats secondhand claims.** `pip index versions <pkg>` queries PyPI
  directly and is the source of truth for what a clean machine (Docker, fresh
  clone) can install. It overrules web searches, docs, and memory. When a
  registry query disagrees with any secondhand source, the registry wins.
- **`--dry-run` + "requirement already satisfied" proves nothing** about whether a
  clean environment can fetch a package — it just found the local copy. Use
  `pip index versions` or `pip install --ignore-installed --no-cache-dir` to force
  a real index check.
- **`requirements.txt` = direct deps only** (the handful you import), not the full
  `pip freeze` tree. Let pip resolve the transitive deps.

---

## D10 launch post (parked — post WITH the repo, not before)

Angle: "AI Engineer" in most listings = reliable backend systems around LLMs, not
ML research. Let the build be the argument; keep any critique implicit.
