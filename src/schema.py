"""
Trade confirmation extraction schema (Pydantic v2).

Type layer only: field types + constraints + enums. Cross-field business
rules (unit coherence, notional = price x quantity, date ordering) attach as
@model_validators in the NEXT block — their signatures are listed at the bottom.

Design notes:
- Decimal everywhere for money/quantity/price. Never float in a trade doc.
- Price is decomposed into (value, currency, per_unit) and Quantity into
  (value, unit). Keeping price.per_unit and quantity.unit as separate typed
  fields is what makes the Day 2 "price unit vs quantity unit" conflation
  *checkable* next block, instead of silently valid.
- extra="forbid": a hallucinated/extra field becomes a validation error that
  feeds the repair loop, rather than passing through unnoticed.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


# --- constrained scalar types ------------------------------------------------

CurrencyCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]  # ISO 4217
LEICode = Annotated[str, StringConstraints(pattern=r"^[A-Z0-9]{20}$")]   # ISO 17442


# --- enums -------------------------------------------------------------------

class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class TradeType(str, Enum):
    PHYSICAL = "PHYSICAL"
    FINANCIAL = "FINANCIAL"


class QuantityUnit(str, Enum):
    BARREL = "BBL"
    METRIC_TON = "MT"
    GALLON = "GAL"
    MMBTU = "MMBTU"
    THERM = "THM"
    MWH = "MWH"
    CUBIC_METER = "M3"


# --- component models --------------------------------------------------------

class Party(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(..., min_length=1)
    lei: Optional[LEICode] = None


class Quantity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: Decimal = Field(..., gt=0)
    unit: QuantityUnit


class Price(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: Decimal = Field(..., gt=0)
    currency: CurrencyCode
    per_unit: QuantityUnit  # "USD per BBL" -> currency=USD, per_unit=BBL


# --- root document -----------------------------------------------------------

class TradeConfirmation(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    confirmation_id: str = Field(..., min_length=1)
    trade_type: TradeType
    side: Side
    commodity: str = Field(..., min_length=1)  # e.g. "WTI Crude Oil"

    trade_date: date
    settlement_date: date

    buyer: Party
    seller: Party

    quantity: Quantity
    price: Price
    notional: Decimal = Field(..., gt=0)
    notional_currency: CurrencyCode

    # optional / physical-delivery fields
    delivery_location: Optional[str] = None
    delivery_period_start: Optional[date] = None
    delivery_period_end: Optional[date] = None


# --- business-rule validators: NEXT BLOCK (Wed 2:00-2:45), not implemented yet
# Attach as @model_validator(mode="after") on TradeConfirmation:
#   1. unit coherence     -> price.per_unit == quantity.unit
#   2. notional check     -> abs(notional - price.value * quantity.value) <= tol
#   3. currency coherence -> price.currency == notional_currency
#   4. date ordering      -> trade_date <= settlement_date
#   5. delivery window    -> start <= end when both present; required if PHYSICAL


if __name__ == "__main__":
    # smoke test: one valid doc, one that trips several type constraints
    good = TradeConfirmation(
        confirmation_id="TC-001",
        trade_type="PHYSICAL",
        side="BUY",
        commodity="WTI Crude Oil",
        trade_date="2026-07-20",
        settlement_date="2026-07-24",
        buyer={"name": "Acme Energy LLC"},
        seller={"name": "Globex Trading"},
        quantity={"value": "1000", "unit": "BBL"},
        price={"value": "82.50", "currency": "USD", "per_unit": "BBL"},
        notional="82500.00",
        notional_currency="USD",
    )
    print("VALID:\n", good.model_dump_json(indent=2))

    try:
        TradeConfirmation(
            confirmation_id="",                 # min_length
            trade_type="SPOT",                  # not a TradeType
            side="BUY",
            commodity="WTI",
            trade_date="2026-07-20",
            settlement_date="2026-07-24",
            buyer={"name": "A"},
            seller={"name": "B"},
            quantity={"value": "-5", "unit": "BBL"},                  # gt=0
            price={"value": "82.5", "currency": "usd", "per_unit": "BBL"},  # pattern
            notional="82500",
            notional_currency="USD",
        )
    except Exception as e:
        print("\nREJECTED AS EXPECTED:\n", e)
