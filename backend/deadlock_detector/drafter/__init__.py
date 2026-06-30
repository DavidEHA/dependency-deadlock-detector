"""Drafters turn an EscalationContext into a human-ready nudge message."""
from __future__ import annotations

from .base import Drafter, EscalationContext
from .claude_foundry import ClaudeFoundryDrafter
from .gemini import GeminiDrafter
from .template import TemplateDrafter

__all__ = [
    "Drafter",
    "EscalationContext",
    "TemplateDrafter",
    "ClaudeFoundryDrafter",
    "GeminiDrafter",
    "select_drafter",
]


def select_drafter() -> Drafter:
    """Pick the best available drafter and fall back gracefully — model-agnostic
    by design (no vendor lock-in): Claude on Azure Foundry (production) if
    configured, else Gemini (free tier) if configured, else the $0 template.
    """
    for drafter in (ClaudeFoundryDrafter(), GeminiDrafter()):
        if getattr(drafter, "is_live", False):
            return drafter
    return TemplateDrafter()
