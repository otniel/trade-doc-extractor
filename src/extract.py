"""
Extraction with a validation-driven repair loop.

extract() makes one LLM call, validates the result against TradeConfirmation,
and on any JSON or validation failure re-prompts the model with the *specific*
errors plus its own previous output. Capped at `max_repairs` retries; on
exhaustion it returns an unresolved result carrying the full attempt trace,
rather than raising — the caller (and the eval) decides what to do with a miss.

The LLM is injected as a plain Callable[[str], str] so the loop is testable
without the network and swappable for any provider.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Callable, Optional

from pydantic import ValidationError

from schema import TradeConfirmation

LLM = Callable[[str], str]

_FENCE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.MULTILINE)


def _strip_fences(text: str) -> str:
    return _FENCE.sub("", text).strip()


def _format_errors(exc: Exception) -> list[str]:
    if isinstance(exc, json.JSONDecodeError):
        return [f"response is not valid JSON: {exc}"]
    if isinstance(exc, ValidationError):
        msgs = []
        for err in exc.errors():
            loc = ".".join(str(p) for p in err["loc"]) or "(root)"
            msgs.append(f"{loc}: {err['msg']}")
        return msgs
    return [str(exc)]


@dataclass
class Attempt:
    n: int
    raw: str
    errors: Optional[list[str]]  # None means this attempt validated


@dataclass
class ExtractionResult:
    ok: bool
    document: Optional[TradeConfirmation]
    attempts: list[Attempt] = field(default_factory=list)

    @property
    def errors(self) -> list[str]:
        return (self.attempts[-1].errors or []) if self.attempts else []

    @property
    def repairs_used(self) -> int:
        return max(0, len(self.attempts) - 1)


_SCHEMA_HINT = """Return ONLY a JSON object with these fields:
  confirmation_id (str), trade_type ("PHYSICAL"|"FINANCIAL"), side ("BUY"|"SELL"),
  commodity (str), trade_date & settlement_date (YYYY-MM-DD),
  buyer & seller ({name, lei?}),
  quantity ({value, unit}), price ({value, currency, per_unit}),
  notional (number), notional_currency (3-letter ISO code),
  delivery_location?, delivery_period_start? & delivery_period_end? (YYYY-MM-DD).
Units must be one of: BBL, MT, GAL, MMBTU, THM, MWH, M3.
Rules: price.per_unit must equal quantity.unit; notional must equal
price.value * quantity.value; PHYSICAL trades need a delivery_location.
No prose, no code fences."""


def _initial_prompt(doc_text: str) -> str:
    return f"Extract the trade confirmation as JSON.\n\n{_SCHEMA_HINT}\n\nDOCUMENT:\n{doc_text}"


def _repair_prompt(doc_text: str, previous: str, errors: str) -> str:
    return (
        "Your previous extraction failed validation. Fix ONLY the listed "
        "problems and return the full corrected JSON object.\n\n"
        f"VALIDATION ERRORS:\n{errors}\n\n"
        f"YOUR PREVIOUS OUTPUT:\n{previous}\n\n"
        f"{_SCHEMA_HINT}\n\nDOCUMENT:\n{doc_text}"
    )


def extract(doc_text: str, llm: LLM, max_repairs: int = 2) -> ExtractionResult:
    attempts: list[Attempt] = []
    raw = llm(_initial_prompt(doc_text))

    for n in range(max_repairs + 1):
        try:
            data = json.loads(_strip_fences(raw))
            doc = TradeConfirmation(**data)
        except (json.JSONDecodeError, ValidationError) as exc:
            errs = _format_errors(exc)
            attempts.append(Attempt(n, raw, errs))
            if n == max_repairs:
                return ExtractionResult(ok=False, document=None, attempts=attempts)
            raw = llm(_repair_prompt(doc_text, raw, "\n".join(errs)))
        else:
            attempts.append(Attempt(n, raw, None))
            return ExtractionResult(ok=True, document=doc, attempts=attempts)

    return ExtractionResult(ok=False, document=None, attempts=attempts)  # unreachable
