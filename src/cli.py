"""CLI entry point: PDF path -> graph -> JSON on stdout.

    PYTHONPATH=src python -m cli documents/trade_confirmation_001.pdf
    make run FILE=documents/trade_confirmation_001.pdf
"""

from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

from pdf import extract_text
from llm import anthropic_llm
from graph import build_graph, run


def main(argv=None) -> int:
    load_dotenv()  # ANTHROPIC_API_KEY from .env; no shell export needed

    ap = argparse.ArgumentParser(description="Extract a trade confirmation from a PDF.")
    ap.add_argument("pdf", help="path to the trade-document PDF")
    ap.add_argument("--max-repairs", type=int, default=2)
    ap.add_argument("--model", default="claude-sonnet-4-6")
    args = ap.parse_args(argv)

    text = extract_text(args.pdf)
    graph = build_graph(anthropic_llm(model=args.model), max_repairs=args.max_repairs)
    result = run(graph, text)

    if result.ok:
        print(result.document.model_dump_json(indent=2))
        return 0

    print(f"EXTRACTION UNRESOLVED after {result.repairs_used} repair(s):", file=sys.stderr)
    for e in result.errors:
        print(f"  - {e}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
