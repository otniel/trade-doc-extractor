"""
LangGraph wiring for the extraction pipeline.

    START -> extract -> validate --(errors & budget left)--> repair -> validate
                             |                                           ^
                             |                                           |
                             +--(ok, or repairs exhausted)--> END        +--(loop)

One conditional edge, off `validate`, routes on the validation result:
  - no errors            -> END (success)
  - errors, budget left  -> repair (then back to validate)
  - errors, budget spent -> END (unresolved)

The graph is a thin state machine over the parse/validate/prompt helpers in
extract.py — the loop logic lives in one place, this just sequences it and
records a trace. LLM is bound at build time via build_graph(llm), keeping the
state a pure data object.
"""

from __future__ import annotations

import json
from typing import Optional, TypedDict

from pydantic import ValidationError
from langgraph.graph import StateGraph, START, END

from schema import TradeConfirmation
from extract import (
    LLM,
    Attempt,
    ExtractionResult,
    _format_errors,
    _initial_prompt,
    _repair_prompt,
    _strip_fences,
)


class GraphState(TypedDict, total=False):
    doc_text: str          # input
    raw: str               # latest LLM output
    document: Optional[TradeConfirmation]
    errors: list[str]
    attempts: list[Attempt]
    repairs_used: int
    max_repairs: int


def build_graph(llm: LLM, max_repairs: int = 2):
    def extract_node(state: GraphState) -> GraphState:
        raw = llm(_initial_prompt(state["doc_text"]))
        return {"raw": raw, "attempts": [], "repairs_used": 0,
                "max_repairs": max_repairs}

    def validate_node(state: GraphState) -> GraphState:
        n = state.get("repairs_used", 0)
        try:
            data = json.loads(_strip_fences(state["raw"]))
            doc = TradeConfirmation(**data)
        except (json.JSONDecodeError, ValidationError) as exc:
            errs = _format_errors(exc)
            return {"document": None, "errors": errs,
                    "attempts": state.get("attempts", []) + [Attempt(n, state["raw"], errs)]}
        return {"document": doc, "errors": [],
                "attempts": state.get("attempts", []) + [Attempt(n, state["raw"], None)]}

    def repair_node(state: GraphState) -> GraphState:
        raw = llm(_repair_prompt(state["doc_text"], state["raw"], "\n".join(state["errors"])))
        return {"raw": raw, "repairs_used": state.get("repairs_used", 0) + 1}

    def route(state: GraphState) -> str:
        if not state["errors"]:
            return "done"
        if state.get("repairs_used", 0) >= state["max_repairs"]:
            return "done"
        return "repair"

    g = StateGraph(GraphState)
    g.add_node("extract", extract_node)
    g.add_node("validate", validate_node)
    g.add_node("repair", repair_node)
    g.add_edge(START, "extract")
    g.add_edge("extract", "validate")
    g.add_conditional_edges("validate", route, {"repair": "repair", "done": END})
    g.add_edge("repair", "validate")
    return g.compile()


def run(graph, doc_text: str) -> ExtractionResult:
    """Invoke the compiled graph and adapt the final state to ExtractionResult,
    so graph and plain-loop callers return the same type."""
    final = graph.invoke({"doc_text": doc_text})
    return ExtractionResult(
        ok=final.get("document") is not None,
        document=final.get("document"),
        attempts=final.get("attempts", []),
    )
