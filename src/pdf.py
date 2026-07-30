"""PDF text extraction via PyMuPDF (the Day 2 happy path)."""

from __future__ import annotations

import fitz  # PyMuPDF


def extract_text(path: str) -> str:
    doc = fitz.open(path)
    try:
        return "\n".join(page.get_text() for page in doc)
    finally:
        doc.close()
