"""Drafter backed by Claude on Azure AI Foundry (Microsoft Foundry).

"Claude via Azure" means Microsoft Foundry, NOT Azure OpenAI (that's GPT-only).
Claude is GA on Foundry via serverless deployment (regions East US2 /
Sweden Central). We use the dedicated `AnthropicFoundry` client, configured
with either the Foundry resource name or the full base URL.

Degrades gracefully: if the `anthropic` SDK or the Foundry credentials are
missing, it falls back to the template drafter so the demo always runs.
"""
from __future__ import annotations

import os

from .base import Drafter, EscalationContext
from .template import TemplateDrafter

_SYSTEM = (
    "You are an assistant to a software delivery lead. Draft a concise, "
    "professional, context-rich escalation nudge for a stalled dependency. "
    "Be specific and actionable, never blaming. Address the owner directly. "
    "Keep it under 120 words, plain text suitable for a Jira comment."
)


class ClaudeFoundryDrafter:
    name = "claude-foundry"
    label = "Claude on Azure Foundry"

    def __init__(self, model: str | None = None, fallback: Drafter | None = None):
        # Haiku 4.5 is the cost-optimal choice for short drafting (team decision).
        # Set FOUNDRY_CLAUDE_MODEL=claude-opus-4-8 for maximum quality.
        self.model = model or os.getenv("FOUNDRY_CLAUDE_MODEL", "claude-haiku-4-5")
        self.fallback: Drafter = fallback or TemplateDrafter()
        self._client = self._build_client()
        self.is_live = self._client is not None

    def _build_client(self):
        try:
            from anthropic import AnthropicFoundry
        except Exception:
            return None
        api_key = os.getenv("AZURE_FOUNDRY_API_KEY")
        resource = os.getenv("AZURE_FOUNDRY_RESOURCE")   # resource NAME, e.g. my-foundry-res
        base_url = os.getenv("AZURE_FOUNDRY_BASE_URL")   # alternative to resource name
        if not api_key or not (resource or base_url):
            return None
        try:
            if base_url:
                return AnthropicFoundry(api_key=api_key, base_url=base_url)
            return AnthropicFoundry(api_key=api_key, resource=resource)
        except Exception:
            return None

    def draft(self, ctx: EscalationContext) -> str:
        if self._client is None:
            return self.fallback.draft(ctx)
        try:
            msg = self._client.messages.create(
                model=self.model,
                max_tokens=400,
                system=_SYSTEM,
                messages=[{"role": "user", "content": _facts(ctx)}],
            )
            text = "".join(
                b.text for b in msg.content if getattr(b, "type", None) == "text"
            ).strip()
            return text or self.fallback.draft(ctx)
        except Exception:
            # Never let a transient LLM error break the pipeline.
            return self.fallback.draft(ctx)


def _facts(ctx: EscalationContext) -> str:
    t = ctx.stale_ticket
    lines = [
        f"Stalled dependency: {t.key} — {t.summary}",
        f"Type: {t.dep_type.value}; current status: {t.status}",
        f"Owner: {t.owner.name} (@{t.owner.handle}), timezone {t.owner.timezone}",
        f"No activity for {ctx.business_days_stale:.1f} working days "
        f"(threshold {t.dep_type.threshold_business_days:.0f}).",
        f"Dependency chain: {' -> '.join(ctx.chain_preview)}",
        f"Blocks {len(ctx.blocked_keys)} downstream tickets across teams: "
        f"{', '.join(ctx.affected_teams)}.",
    ]
    if ctx.days_to_milestone is not None and t.milestone:
        lines.append(f"Milestone '{t.milestone}' due in {ctx.days_to_milestone:.0f} days.")
    lines.append(f"Severity: {ctx.severity.level.value} (score {ctx.severity.score}).")
    lines.append("Write the escalation nudge now.")
    return "\n".join(lines)
