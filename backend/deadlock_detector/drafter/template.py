"""$0 fallback drafter — deterministic, no LLM. Always available.

The LLM only raises message quality; the system never *depends* on it.
"""
from __future__ import annotations

from .base import EscalationContext


class TemplateDrafter:
    name = "template"
    is_live = False
    label = "Template (rule-based, $0)"

    def draft(self, ctx: EscalationContext) -> str:
        t = ctx.stale_ticket
        chain = " -> ".join(ctx.chain_preview)
        teams = ", ".join(ctx.affected_teams)
        milestone = t.milestone or "the current sprint"
        days_ms = (
            f"{ctx.days_to_milestone:.0f} day(s)"
            if ctx.days_to_milestone is not None
            else "soon"
        )
        dep_label = t.dep_type.value.replace("_", " ")
        return (
            f"@{t.owner.handle}: {t.key} ({t.summary}) has had no activity for "
            f"{ctx.business_days_stale:.1f} working day(s) in your timezone "
            f"({t.owner.timezone}), past the "
            f"{t.dep_type.threshold_business_days:.0f}-working-day threshold for a "
            f"{dep_label}.\n\n"
            f"Why it matters: it is blocking {len(ctx.blocked_keys)} downstream "
            f"ticket(s) across {teams}. Dependency chain: {chain}. "
            f"Milestone \"{milestone}\" is due in {days_ms} and is now at risk.\n\n"
            f"Suggested next step: please confirm whether {t.key} can be actioned "
            f"today, or point us to who can, so we can unblock {teams} before the "
            f"milestone slips. (Severity: {ctx.severity.level.value}, "
            f"score {ctx.severity.score}.)"
        )
