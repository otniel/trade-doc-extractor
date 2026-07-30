import json

import pytest


@pytest.fixture
def valid_data() -> dict:
    """A fully valid PHYSICAL trade confirmation (units coherent, math checks)."""
    return {
        "confirmation_id": "TC-001",
        "trade_type": "PHYSICAL",
        "side": "BUY",
        "commodity": "WTI Crude Oil",
        "trade_date": "2026-07-20",
        "settlement_date": "2026-07-24",
        "buyer": {"name": "Acme Energy LLC"},
        "seller": {"name": "Globex Trading"},
        "quantity": {"value": "1000", "unit": "BBL"},
        "price": {"value": "82.50", "currency": "USD", "per_unit": "BBL"},
        "notional": "82500.00",
        "notional_currency": "USD",
        "delivery_location": "Cushing, OK",
    }


@pytest.fixture
def good_json(valid_data) -> str:
    return json.dumps(valid_data)


@pytest.fixture
def bad_unit_json(valid_data) -> str:
    """Day 2 failure mode: quantity unit MT while price is per BBL."""
    return json.dumps({**valid_data, "quantity": {"value": "1000", "unit": "MT"}})


class ScriptedLLM:
    """Deterministic fake LLM: returns each scripted response in order."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def __call__(self, prompt: str) -> str:
        self.calls += 1
        return self.responses.pop(0)


@pytest.fixture
def scripted_llm():
    return ScriptedLLM
