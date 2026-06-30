"""End-to-end local demo — no cloud credentials required.

Reproduces the slide's flow:
  silent ticket (4 days) -> 3-node chain stalled -> 7 tickets blocked
  -> sprint at risk -> escalation drafted -> sprint saved.

Run from the repo root:  python run_demo.py
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from deadlock_detector.drafter.claude_foundry import ClaudeFoundryDrafter
from deadlock_detector.ingest.jira_mock import MockJiraIngestor
from deadlock_detector.notifier.console import ConsoleNotifier
from deadlock_detector.pipeline import Pipeline

# Fixed "now" so the numbers are stable in a live presentation (a Wednesday).
NOW = datetime(2026, 6, 24, 14, 0, tzinfo=timezone.utc)
DATA = Path(__file__).parent / "data" / "mock_jira.json"


def main() -> None:
    ingestor = MockJiraIngestor(DATA)
    drafter = ClaudeFoundryDrafter()        # falls back to template without creds
    notifier = ConsoleNotifier()
    pipeline = Pipeline(ingestor, drafter, notifier)

    backend = "Claude on Azure Foundry" if drafter._client else "template fallback (no Foundry creds)"
    print("\nDependency Deadlock Detector - demo")
    print(f"  scan time (UTC): {NOW.isoformat()}")
    print(f"  drafter backend: {drafter.name}  [{backend}]")

    escalations = pipeline.run(now=NOW)

    if not escalations:
        print("\nNo stale dependencies. Nothing to escalate.\n")
        return

    for esc in escalations:
        c = esc.context
        print(
            f"DETECTED: {c.stale_ticket.key} silent {c.business_days_stale:.1f} "
            f"working days -> chain {' -> '.join(c.chain_preview)} -> "
            f"{len(c.blocked_keys)} tickets blocked -> "
            f"severity {c.severity.level.value} (score {c.severity.score})"
        )

    print(f"{len(escalations)} escalation(s) drafted and ready for one-click approval. Sprint saved.\n")


if __name__ == "__main__":
    main()
