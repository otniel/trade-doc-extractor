"""
Trade confirmation extraction schema (Pydantic v2).

Type layer + cross-field business rules. The business rules are what turn
plausible-but-wrong LLM extractions (right shape, wrong values) into caught
validation errors that feed the repair loop.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Annotated, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)


# --- constrained scalar types ------------------------------------------------

CurrencyCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]  # ISO 4217
LEICode = Annotated[str, StringConstraints(pattern=r"^[A-Z0-9]{20}$")]   # ISO 17442

# notional tolerance: 0.5% relative, floored at one cent. Wide enough to absorb
# rounding in the source doc, tight enough to catch a unit/order-of-magnitude error.
NOTIONAL_REL_TOL = Decimal("0.005")


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

    delivery_location: Optional[str] = None
    delivery_period_start: Optional[date] = None
    delivery_period_end: Optional[date] = None

    @model_validator(mode="after")
    def _business_rules(self) -> "TradeConfirmation":
        """Collect every violation, then raise once so the repair loop can fix
        all of them in a single round trip instead of one call per rule."""
        issues: list[str] = []

        # 1. unit coherence — the Day 2 bug. Price must be quoted per the same
        #    unit the quantity is measured in.
        if self.price.per_unit != self.quantity.unit:
            issues.append(
                f"unit mismatch: price quoted per {self.price.per_unit.value}, "
                f"but quantity is measured in {self.quantity.unit.value}"
            )

        # 2. currency coherence
        if self.price.currency != self.notional_currency:
            issues.append(
                f"currency mismatch: price in {self.price.currency}, "
                f"notional in {self.notional_currency}"
            )

        # 3. notional ~= price * quantity (tolerant of rounding)
        computed = self.price.value * self.quantity.value
        tol = max(Decimal("0.01"), computed * NOTIONAL_REL_TOL)
        if abs(self.notional - computed) > tol:
            issues.append(
                f"notional {self.notional} != price x quantity ({computed}); "
                f"difference exceeds tolerance {tol}"
            )

        # 4. date ordering
        if self.trade_date > self.settlement_date:
            issues.append(
                f"trade_date {self.trade_date} is after "
                f"settlement_date {self.settlement_date}"
            )

        # 5. delivery window + physical trades must state a delivery location
        s, e = self.delivery_period_start, self.delivery_period_end
        if s and e and s > e:
            issues.append(f"delivery window start {s} is after end {e}")
        if self.trade_type is TradeType.PHYSICAL and not self.delivery_location:
            issues.append("physical trade requires a delivery_location")

        if issues:
            raise ValueError(" | ".join(issues))
        return self
