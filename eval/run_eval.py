"""Eval harness — the centerpiece.

For every golden file in eval/golden/, run the full pipeline over the matching
PDF in documents/ and score field-level accuracy against the golden. Only the
fields present in each golden file are scored (see the golden `_comment`), so
the number reflects what the document can actually be held to.

    make eval
    PYTHONPATH=src python eval/run_eval.py --max-repairs 2

Record the baseline BEFORE trusting the repair loop: run once with
--max-repairs 0, then again with 2, and compare. No baseline = no story.
"""

from __future__ import annotations

import argparse
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from src.graph import build_graph, run

ROOT = Path(__file__).resolve().parent.parent
GOLDEN_DIR = ROOT / "eval" / "golden"
DOCS_DIR = ROOT / "documents"


def flatten(obj, prefix: str = "") -> dict[str, object]:
    """Flatten nested dicts to dot-paths. Ignores keys starting with '_'."""
    out: dict[str, object] = {}
    for k, v in obj.items():
        if k.startswith("_"):
            continue
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.update(flatten(v, key))
        else:
            out[key] = v
    return out


def _eq(pred, gold) -> bool:
    """Numeric-aware, case-insensitive equality (so 1000 == '1000.00')."""
    try:
        return Decimal(str(pred)) == Decimal(str(gold))
    except (InvalidOperation, ValueError):
        return str(pred).strip().lower() == str(gold).strip().lower()


def score(pred: dict, gold: dict) -> tuple[int, int, list[str]]:
    """Score only the leaf fields the golden specifies."""
    flat_pred, flat_gold = flatten(pred), flatten(gold)
    correct, misses = 0, []
    for key, gval in flat_gold.items():
        pval = flat_pred.get(key, "<missing>")
        if _eq(pval, gval):
            correct += 1
        else:
            misses.append(f"{key}: got {pval!r}, expected {gval!r}")
    return correct, len(flat_gold), misses


def main(argv=None) -> int:
    from dotenv import load_dotenv
    from src.pdf import extract_text
    from src.llm import anthropic_llm

    ap = argparse.ArgumentParser(description="Field-level accuracy vs the golden set.")
    ap.add_argument("--max-repairs", type=int, default=2)
    ap.add_argument("--model", default="claude-sonnet-4-6")
    args = ap.parse_args(argv)

    load_dotenv()
    graph = build_graph(anthropic_llm(model=args.model), max_repairs=args.max_repairs)

    golden_files = sorted(GOLDEN_DIR.glob("*.json"))
    if not golden_files:
        print("no golden files in eval/golden/")
        return 1

    total_correct = total_fields = total_repairs = resolved = 0
    print(f"\nmax_repairs={args.max_repairs}  model={args.model}\n" + "-" * 60)

    for gf in golden_files:
        gold = json.loads(gf.read_text())
        pdf = DOCS_DIR / f"{gf.stem}.pdf"
        result = run(graph, extract_text(str(pdf)))

        if not result.ok:
            print(f"{gf.stem:32s} UNRESOLVED ({result.repairs_used} repairs)")
            total_fields += len(flatten(gold))
            continue

        resolved += 1
        total_repairs += result.repairs_used
        pred = result.document.model_dump(mode="json")
        correct, n, misses = score(pred, gold)
        total_correct += correct
        total_fields += n
        print(f"{gf.stem:32s} {correct}/{n} fields  ({result.repairs_used} repairs)")
        for m in misses:
            print(f"    miss: {m}")

    acc = (total_correct / total_fields * 100) if total_fields else 0.0
    print("-" * 60)
    print(f"field-level accuracy: {total_correct}/{total_fields} = {acc:.1f}%")
    print(f"resolved: {resolved}/{len(golden_files)} docs | total repairs: {total_repairs}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
