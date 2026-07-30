"""Anthropic-backed LLM callable, injected into extract()/build_graph().

Kept deliberately thin: the pipeline depends on a str -> str function, not on
the SDK, so this is the only file that imports anthropic.
"""

from __future__ import annotations

import os

from anthropic import Anthropic

from extract import LLM


def anthropic_llm(
    model: str = "claude-sonnet-4-6",
    max_tokens: int = 2000,
    temperature: float = 0.0,          # deterministic extraction
) -> LLM:
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    def _call(prompt: str) -> str:
        resp = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in resp.content if b.type == "text")

    return _call
