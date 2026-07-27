from pydantic import BaseModel
from datetime import date
from typing import Optional

class TradeConfirmation(BaseModel):
    counterparty: str
    trade_date: date
    settlement_date: date
    product: str
    quantity: float
    unit: str
    unit_price: float
    total_value: float
    delivery_terms: Optional[str] = None
    quality_spec: Optional[str] = None

class Invoice(BaseModel):
    invoice_number: str
    invoice_date: date
    due_date: date
    bill_to: str
    line_items: list[dict]
    subtotal: float
    total: float
    payment_terms: Optional[str] = None

class StatementOfAccount(BaseModel):
    account_holder: str
    account_number: str
    period_start: date
    period_end: date
    opening_balance: float
    closing_balance: float
    transactions: list[dict]

class PurchaseOrder(BaseModel):
    po_number: str
    po_date: date
    supplier: str
    buyer: str
    line_items: list[dict]
    total: float
    required_delivery: date
    payment_terms: Optional[str] = None

class Contract(BaseModel):
    contract_id: str
    parties: list[str]
    effective_date: date
    expiration_date: date
    key_terms: dict
    governing_law: Optional[str] = None
