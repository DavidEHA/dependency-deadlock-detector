"""Orchestrates the full pipeline. This is the ~80% deterministic backbone;
the LLM is consulted at exactly one step (drafting), once per new escalation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .dedupe import EscalationLedger
from .drafter.base import Drafter, EscalationContext
from .graph import DependencyGraph
from .ingest.base import Ingestor
from .notifier.base import Notifier
from .severity import score
from .staleness import assess


@dataclass
class Escalation:
    context: EscalationContext
    message: str


class Pipeline:
    def __init__(
        self,
        ingestor: Ingestor,
        drafter: Drafter,
        notifier: Notifier,
        ledger: EscalationLedger | None = None,
    ):
        self.ingestor = ingestor
        self.drafter = drafter
        self.notifier = notifier
        self.ledger = ledger or EscalationLedger()

    def run(self, now: datetime | None = None, notify: bool = True) -> list[Escalation]:
        now = now or datetime.now(timezone.utc)
        tickets = self.ingestor.fetch()
        graph = DependencyGraph(tickets)

        contexts: list[EscalationContext] = []
        for ticket in tickets:
            result = assess(ticket, now)
            if not result.is_stale:
                continue

            blast = graph.blast_radius(ticket.key)
            days_to_milestone = None
            if ticket.milestone_due:
                days_to_milestone = (ticket.milestone_due - now).total_seconds() / 86400.0

            severity = score(
                blast_count=len(blast),
                business_days_stale=result.business_days_stale,
                threshold_business_days=result.threshold_business_days,
                days_to_milestone=days_to_milestone,
            )
            contexts.append(
                EscalationContext(
                    stale_ticket=ticket,
                    business_days_stale=result.business_days_stale,
                    severity=severity,
                    blocked_keys=sorted(blast),
                    affected_teams=sorted(graph.affected_teams(blast)),
                    chain_preview=graph.main_chain(ticket.key),
                    days_to_milestone=days_to_milestone,
                )
            )

        contexts.sort(key=lambda c: c.severity.score, reverse=True)

        escalations: list[Escalation] = []
        for ctx in contexts:
            key = ctx.stale_ticket.key
            if not self.ledger.should_escalate(key, ctx.severity.score):
                continue
            message = self.drafter.draft(ctx)
            if notify:
                self.notifier.send(ctx.stale_ticket, message)
            self.ledger.record(key, ctx.severity.score)
            escalations.append(Escalation(context=ctx, message=message))
        return escalations
