"""Drafter backed by Google Gemini (AI Studio free tier).

A swappable alternative to Claude behind the same `Drafter` interface — that's
the whole point of the interface: the agent is model-agnostic, no vendor
lock-in. Reads GEMINI_API_KEY (free key from https://aistudio.google.com/apikey).
Falls back to the template drafter if the SDK or key is missing.
"""
from __future__ import annotations

import os

from .base import Drafter, EscalationContext
from .claude_foundry import _SYSTEM, _facts  # reuse the same prompt + fact framing
from .template import TemplateDrafter


class GeminiDrafter:
    name = "gemini"
    label = "Gemini (free tier)"

    def __init__(self, model: str | None = None, fallback: Drafter | None = None):
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.fallback: Drafter = fallback or TemplateDrafter()
        self._client = self._build_client()
        self.is_live = self._client is not None

    def _build_client(self):
        try:
            from google import genai
        except Exception:
            return None
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None
        try:
            return genai.Client(api_key=api_key)
        except Exception:
            return None

    def draft(self, ctx: EscalationContext) -> str:
        if self._client is None:
            return self.fallback.draft(ctx)
        try:
            from google.genai import types

            resp = self._client.models.generate_content(
                model=self.model,
                contents=_facts(ctx),
                config=types.GenerateContentConfig(
                    system_instruction=_SYSTEM,
                    max_output_tokens=800,
                    # Disable "thinking": a short nudge doesn't need it, and on
                    # 2.5/3.x flash models the thinking budget otherwise eats the
                    # output tokens and truncates the reply (finish MAX_TOKENS).
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
            )
            text = (resp.text or "").strip()
            return text or self.fallback.draft(ctx)
        except Exception:
            # Never let a transient LLM error break the pipeline.
            return self.fallback.draft(ctx)
