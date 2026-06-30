"""End-to-end local demo — no cloud credentials required.

Reproduces the slide's flow:
  silent ticket (4 days) -> 3-node chain stalled -> 7 tickets blocked
  -> sprint at risk -> escalation drafted -> sprint saved.

Run from the backend/ directory:  python run_demo.py
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

# Load backend/.env (Foundry/Jira creds) if present. Optional dependency — the
# demo works without it, falling back to the template drafter.
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).parent / ".env")
except Exception:
    pass

from deadlock_detector.drafter import select_drafter
from deadlock_detector.ingest.jira_mock import MockJiraIngestor
from deadlock_detector.notifier.console import ConsoleNotifier
from deadlock_detector.pipeline import Pipeline

# Fixed "now" so the numbers are stable in a live presentation (a Wednesday).
NOW = datetime(2026, 6, 24, 14, 0, tzinfo=timezone.utc)
DATA = Path(__file__).parent / "data" / "mock_jira.json"


def main() -> None:
    ingestor = MockJiraIngestor(DATA)
    drafter = select_drafter()              # Foundry -> Gemini -> template
    notifier = ConsoleNotifier()
    pipeline = Pipeline(ingestor, drafter, notifier)

    print("\nDependency Deadlock Detector - demo")
    print(f"  scan time (UTC): {NOW.isoformat()}")
    print(f"  drafter backend: {drafter.label}")

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
