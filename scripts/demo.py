"""
Two-minute, reproducible demo of the extract -> validate -> repair loop.

Runs the REAL pipeline (src.graph's LangGraph state machine, src.schema's
Pydantic business rules) end to end. The only thing scripted is the LLM: it
returns a canned first answer that reproduces the exact Day-2 bug this project
exists to catch (a PRICE unit written into the QUANTITY unit field -- the math
still checks, so nothing would complain without the validator), then a
corrected answer on repair.

Why scripted and not a live API call: measured in eval/run_eval.py against the
real corpus (see NOTES.md, D4), claude-sonnet-4-6 does not reproduce this bug
reliably -- 0 repairs fired across 4 documents, including 3 built specifically
to trigger it. A live demo would be a coin flip. This script instead
demonstrates the loop's *guaranteed* behavior deterministically, the same way
tests/test_extract.py and tests/test_graph.py prove it. For live-model numbers
on the real corpus, run `make eval`.

    make demo
    python -m scripts.demo
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.graph import build_graph, run  # noqa: E402

DOC_TEXT = """
TRADE CONFIRMATION
Confirmation #: DEMO-001
Trade Date: July 20, 2026
Settlement Date: July 24, 2026
Product: WTI Crude Oil
Quantity: 1,000 barrels
Unit: USD per barrel
Price: $82.50
Total Value: $82,500.00
Delivery Terms: FOB Cushing, OK
""".strip()

# What a naive extraction does: reads the PRICE's unit (USD per barrel) into
# the QUANTITY's unit field. 1000 x 82.50 = 82500 still checks out -- the
# error is silent to any naive check, which is exactly the point.
BAD_FIRST_ATTEMPT = json.dumps({
    "confirmation_id": "DEMO-001",
    "trade_type": "PHYSICAL",
    "commodity": "WTI Crude Oil",
    "trade_date": "2026-07-20",
    "settlement_date": "2026-07-24",
    "quantity": {"value": "1000", "unit": "MT"},   # BUG: should be BBL
    "price": {"value": "82.50", "currency": "USD", "per_unit": "BBL"},
    "notional": "82500.00",
    "notional_currency": "USD",
    "delivery_location": "Cushing, OK",
})

CORRECTED_REPAIR = json.dumps({
    "confirmation_id": "DEMO-001",
    "trade_type": "PHYSICAL",
    "commodity": "WTI Crude Oil",
    "trade_date": "2026-07-20",
    "settlement_date": "2026-07-24",
    "quantity": {"value": "1000", "unit": "BBL"},
    "price": {"value": "82.50", "currency": "USD", "per_unit": "BBL"},
    "notional": "82500.00",
    "notional_currency": "USD",
    "delivery_location": "Cushing, OK",
})


def scripted_llm(responses: list[str]):
    """A minimal deterministic stand-in for src.llm.anthropic_llm: same
    Callable[[str], str] contract the real pipeline expects, no network."""
    calls = iter(responses)

    def _call(prompt: str) -> str:
        return next(calls)

    return _call


def banner(text: str) -> None:
    print("\n" + "=" * 72)
    print(text)
    print("=" * 72)


def main() -> int:
    banner(
        "DEMO MODE -- scripted LLM, no ANTHROPIC_API_KEY or network required.\n"
        "Reproduces the exact Day-2 bug on purpose: a PRICE unit written into\n"
        "the QUANTITY unit field. Math still checks (1000 x 82.50 = 82,500),\n"
        "so this would be silent without the validator below.\n"
        "For live-model numbers on the real corpus: make eval"
    )

    print("\nINPUT DOCUMENT:")
    print(DOC_TEXT)

    llm = scripted_llm([BAD_FIRST_ATTEMPT, CORRECTED_REPAIR])
    graph = build_graph(llm, max_repairs=2)
    result = run(graph, DOC_TEXT)

    for i, attempt in enumerate(result.attempts, start=1):
        banner(f"ATTEMPT {i}")
        print("LLM output:")
        print(json.dumps(json.loads(attempt.raw), indent=2))
        if attempt.errors:
            print("\nVALIDATION: FAILED")
            for e in attempt.errors:
                print(f"  - {e}")
            print("\n-> repairing: re-prompting with the specific error(s) above")
        else:
            print("\nVALIDATION: PASSED")

    banner("RESULT")
    if result.ok:
        print(f"Extraction succeeded after {result.repairs_used} repair(s).\n")
        print(result.document.model_dump_json(indent=2))
        return 0
    print(f"UNRESOLVED after {result.repairs_used} repair(s):")
    for e in result.errors:
        print(f"  - {e}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
