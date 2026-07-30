"""
One-off generator for the Day-4 messy corpus (documents/trade_confirmation_00{2,3,4}.pdf).

Not part of the pipeline -- run once to produce the PDFs, then keep the PDFs
in version control (documents/ is data, not code). Kept for reproducibility:
if a doc needs to be regenerated or a fourth added, edit DOCS below and rerun.

    python scripts/generate_corpus_docs.py

Each doc mirrors the visual style of the original hand-authored
trade_confirmation_001.pdf (Helvetica 11, "====" section rules, padded
"Label:  value" lines) but is built with an explicit ground truth AND an
explicit trap: a layout pattern designed to tempt an LLM into the same class
of silent error the pipeline exists to catch (unit conflation, an
enum-invalid decoy unit, a decoy currency figure next to notional).
"""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "documents"

RULE = "=" * 72  # fits the 468pt box width at Helvetica 11 without auto-wrap

DOC_002 = f"""{RULE}
                           TRADE CONFIRMATION
{RULE}

Trade Date:           July 18, 2026
Settlement Date:      August 18, 2026
Confirmation #:       TC-2026-0498

{RULE}
COUNTERPARTY DETAILS
{RULE}
Counterparty Name:    NextEra Power Marketing LLC
Counterparty Code:    NEXTERA-PWR-014
Contact Person:       Diane Okafor
Email:                d.okafor@nexterapower.com
Telephone:            +1 561 555 0142

{RULE}
PARTIES
{RULE}
Buyer:                Meridian Grid Solutions Inc.
Seller:               NextEra Power Marketing LLC
Side (buyer's view):  BUY

{RULE}
TRANSACTION DETAILS
{RULE}
Product:              PJM Western Hub Power (Financial Swap)
Trade Type:           Financial swap, cash-settled against PJM Western Hub
                      day-ahead LMP -- no physical delivery obligation
Notional Volume:      20,000 (20,000,000 kWh equivalent)
Unit of Measure:      MWh
Fixed Price:          $42.75 per MWh
Total Notional Value: $855,000.00

Settlement Terms:     Cash settlement only; no physical delivery of power
Reference Index:      PJM Western Hub Day-Ahead LMP
Calculation Agent:    NextEra Power Marketing LLC

{RULE}
PAYMENT TERMS
{RULE}
Payment Method:       Wire Transfer, T+2
Due Date:             August 18, 2026
Bank Account:         IBAN: US00NEXT0000123456789
Bank Name:            JPMorgan Chase, New York
BIC/SWIFT:            CHASUS33

{RULE}
SPECIAL TERMS & CONDITIONS
{RULE}
- Cash-settled financial swap; no physical delivery of power occurs
- Governed by ISDA Master Agreement (2002) and Schedule
- Settlement amount = (Fixed Price - Floating Price) x Notional Volume
- Force majeure per ISDA Master Agreement Section 5

{RULE}
AUTHORIZED SIGNATURES
{RULE}

For Seller:                        For Buyer:

_______________________            _______________________
Signature                          Signature
Name: Diane Okafor                 Name: Marcus Bell
Title: Senior Trader                Title: Head of Trading
Date: July 18, 2026                 Date: July 18, 2026

{RULE}
"""

DOC_003 = f"""{RULE}
                           TRADE CONFIRMATION
{RULE}

Trade Date:           July 10, 2026
Settlement Date:      July 24, 2026
Confirmation #:       TC-2026-0533

{RULE}
COUNTERPARTY DETAILS
{RULE}
Counterparty Name:    Andes Metals Trading S.A.
Counterparty Code:    ANDES-LATAM-007
Contact Person:       Rafael Ibanez
Email:                r.ibanez@andesmetals.com
Telephone:            +56 2 2345 6789

{RULE}
PARTIES
{RULE}
Buyer:                Continental Copper Refiners Ltd.
Seller:               Andes Metals Trading S.A.
Side (buyer's view):  BUY

{RULE}
TRANSACTION DETAILS
{RULE}
Product:              Copper Cathode Grade A (LME Registered)
Quantity:             500 (1,102,311 lbs gross)
Unit:                 USD per metric ton
Price:                $9,450.00
Total Value:          $4,725,000.00

Delivery Terms:       CIF Antwerp
Quality Grade:        LME Grade A, min. 99.9935% Cu
Incoterms:            2020 CIF

{RULE}
PAYMENT TERMS
{RULE}
Payment Method:       Bank Wire Transfer
Due Date:             July 24, 2026
Bank Account:         IBAN: CL0012345678901234567890
Bank Name:            Banco Santander Chile, Santiago
BIC/SWIFT:            BSCHCLRM

{RULE}
LOADING & DELIVERY SCHEDULE
{RULE}
Loading Port:         Valparaiso, Chile
Loading Vessel:       MV Atacama Star
Estimated B/L Date:   July 15, 2026
Discharge Port:       Port of Antwerp
ETA Discharge:        August 2, 2026

{RULE}
SPECIAL TERMS & CONDITIONS
{RULE}
- Price subject to LME Official Cash Settlement adjustment
- Quality specifications per LME Grade A standard
- Force majeure clause applicable per ICC Force Majeure Clause 2020
- Late payment penalty: 1.5% per month

{RULE}
AUTHORIZED SIGNATURES
{RULE}

For Seller:                        For Buyer:

_______________________            _______________________
Signature                          Signature
Name: Rafael Ibanez                Name: Priya Nandan
Title: Trading Director            Title: Procurement Manager
Date: July 10, 2026                Date: July 10, 2026

{RULE}
"""

DOC_004 = f"""{RULE}
                           TRADE CONFIRMATION
{RULE}

Trade Date:           July 15, 2026
Settlement Date:      August 15, 2026
Confirmation #:       TC-2026-0512

{RULE}
COUNTERPARTY DETAILS
{RULE}
Counterparty Name:    Meridian Gas Marketing LLC
Counterparty Code:    MERIDIAN-GAS-022
Contact Person:       Laura Whitfield
Email:                l.whitfield@meridiangas.com
Telephone:            +1 713 555 0198

{RULE}
PARTIES
{RULE}
Buyer:                Gulf Coast Energy Partners LLC
Seller:               Meridian Gas Marketing LLC
Side (buyer's view):  BUY

{RULE}
TRANSACTION DETAILS
{RULE}
Product:              Henry Hub Natural Gas Forward
Quantity:             50,000 MMBtu (approx. 51.28 million standard cubic feet)
Unit:                 USD per MMBtu
Price:                $3.85
Total Value:          $192,500.00 (approx. EUR 178,325 at reference FX 0.9264)

Delivery Terms:       Henry Hub, Erath, Louisiana
Quality Grade:        Pipeline-quality per GPA 2145
Incoterms:            N/A (pipeline delivery)

{RULE}
PAYMENT TERMS
{RULE}
Payment Method:       Bank Wire Transfer
Due Date:             August 15, 2026
Bank Account:         IBAN: US00MERI0000987654321
Bank Name:            Wells Fargo Bank, Houston
BIC/SWIFT:            WFBIUS6S

{RULE}
LOADING & DELIVERY SCHEDULE
{RULE}
Delivery Point:       Henry Hub, Erath, Louisiana
Nomination Deadline:  August 13, 2026
Flow Period:          August 15-31, 2026

{RULE}
SPECIAL TERMS & CONDITIONS
{RULE}
- Price subject to NYMEX Henry Hub settlement adjustment
- Quality specifications per GPA 2145 standard
- Force majeure clause applicable per NAESB Base Contract
- Late payment penalty: 2% per month

{RULE}
AUTHORIZED SIGNATURES
{RULE}

For Seller:                        For Buyer:

_______________________            _______________________
Signature                          Signature
Name: Laura Whitfield              Name: Tom Reyes
Title: Trading Manager             Title: Gas Supply Manager
Date: July 15, 2026                Date: July 15, 2026

{RULE}
"""

DOCS = {
    "trade_confirmation_002.pdf": DOC_002,
    "trade_confirmation_003.pdf": DOC_003,
    "trade_confirmation_004.pdf": DOC_004,
}


PAGE_W, PAGE_H = 612, 792
MARGIN = 72
FONTSIZE = 11
LINES_PER_PAGE = 38  # empirically fits a 666pt-tall box at Helvetica 11 with margin


def render(text: str, path: Path) -> None:
    """Paginate manually: insert_textbox silently drops all text if it
    overflows a single box, so split into page-sized line chunks up front."""
    lines = text.splitlines()
    pages = [lines[i:i + LINES_PER_PAGE] for i in range(0, len(lines), LINES_PER_PAGE)] or [[]]

    doc = fitz.open()
    rect = fitz.Rect(MARGIN, MARGIN - 18, PAGE_W - MARGIN, PAGE_H - MARGIN)
    for chunk in pages:
        page = doc.new_page(width=PAGE_W, height=PAGE_H)
        rc = page.insert_textbox(rect, "\n".join(chunk), fontsize=FONTSIZE, fontname="helv", align=0)
        if rc < 0:
            raise ValueError(f"page overflow rendering {path.name}: surplus {rc}")
    doc.save(path)
    doc.close()


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    for name, text in DOCS.items():
        render(text, OUT_DIR / name)
        print(f"wrote {name}")


if __name__ == "__main__":
    main()
