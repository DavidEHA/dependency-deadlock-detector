"""Demo notifier — prints the escalation as it would appear before approval."""
from __future__ import annotations

from ..models import Ticket


class ConsoleNotifier:
    name = "console"

    def send(self, ticket: Ticket, message: str) -> None:
        bar = "=" * 72
        print(f"\n{bar}")
        print(f"  ESCALATION  ->  Jira comment on {ticket.key}  (@{ticket.owner.handle})")
        print(bar)
        print(message)
        print(f"{bar}\n")
