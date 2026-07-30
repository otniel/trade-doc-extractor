import pytest
from pydantic import ValidationError

from src.schema import Side, TradeConfirmation


def over(data, **changes):
    return {**data, **changes}


def test_valid_doc_parses(valid_data):
    doc = TradeConfirmation(**valid_data)
    assert doc.quantity.unit == doc.price.per_unit


# --- buyer/seller/side are optional (D4: forcing them caused fabrication on
# docs that only name one counterparty and never state a side) ---
def test_buyer_seller_side_optional(valid_data):
    data = {k: v for k, v in valid_data.items() if k not in ("buyer", "seller", "side")}
    doc = TradeConfirmation(**data)
    assert doc.buyer is None and doc.seller is None and doc.side is None


def test_buyer_seller_side_populated_when_present(valid_data):
    doc = TradeConfirmation(**valid_data)
    assert doc.buyer.name == "Acme Energy LLC" and doc.side == Side.BUY


# --- type-layer constraints ---
def test_negative_quantity_rejected(valid_data):
    with pytest.raises(ValidationError):
        TradeConfirmation(**over(valid_data, quantity={"value": "-5", "unit": "BBL"}))


def test_bad_enum_rejected(valid_data):
    with pytest.raises(ValidationError):
        TradeConfirmation(**over(valid_data, trade_type="SPOT"))


def test_lowercase_currency_rejected(valid_data):
    with pytest.raises(ValidationError):
        TradeConfirmation(**over(valid_data, notional_currency="usd"))


# --- business rules ---
def test_unit_conflation_rejected(valid_data):
    with pytest.raises(ValidationError, match="unit mismatch"):
        TradeConfirmation(**over(valid_data, quantity={"value": "1000", "unit": "MT"}))


def test_notional_mismatch_rejected(valid_data):
    with pytest.raises(ValidationError, match="notional"):
        TradeConfirmation(**over(valid_data, notional="825000.00"))


def test_currency_mismatch_rejected(valid_data):
    with pytest.raises(ValidationError, match="currency mismatch"):
        TradeConfirmation(**over(valid_data, notional_currency="EUR"))


def test_dates_reversed_rejected(valid_data):
    with pytest.raises(ValidationError, match="after settlement_date"):
        TradeConfirmation(**over(valid_data, trade_date="2026-07-25"))


def test_physical_requires_delivery_location(valid_data):
    with pytest.raises(ValidationError, match="delivery_location"):
        TradeConfirmation(**over(valid_data, delivery_location=None))


def test_financial_needs_no_delivery_location(valid_data):
    doc = TradeConfirmation(**over(valid_data, trade_type="FINANCIAL", delivery_location=None))
    assert doc.trade_type.value == "FINANCIAL"


def test_notional_within_tolerance_passes(valid_data):
    # off by one cent -> inside the 0.5% floor of 0.01, should pass
    TradeConfirmation(**over(valid_data, notional="82500.01"))
