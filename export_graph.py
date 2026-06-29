"""Export the agent's analysis to a static graph for the demo visualization.

Produces viz/graph_data.js (`window.GRAPH_DATA = {...}`). Open viz/index.html
in a browser afterwards. The visualization is read-only and demo-only: it
consumes the agent's JSON and recomputes nothing itself.

Run from the repo root:  python export_graph.py
"""
from __future__ import annotations

import json
from pathlib import Path

from deadlock_detector.drafter.claude_foundry import ClaudeFoundryDrafter
from deadlock_detector.graph import DependencyGraph
from deadlock_detector.ingest.jira_mock import MockJiraIngestor
from deadlock_detector.notifier.console import ConsoleNotifier
from deadlock_detector.pipeline import Pipeline
from deadlock_detector.staleness import assess
from run_demo import DATA, NOW

OUT = Path(__file__).parent / "viz" / "graph_data.js"


def build() -> None:
    ingestor = MockJiraIngestor(DATA)
    tickets = ingestor.fetch()

    escalations = Pipeline(ingestor, ClaudeFoundryDrafter(), ConsoleNotifier()).run(
        now=NOW, notify=False
    )
    roots = {e.context.stale_ticket.key: e for e in escalations}
    blast_union: set[str] = set()
    for e in escalations:
        blast_union |= set(e.context.blocked_keys)

    nodes = []
    for t in tickets:
        s = assess(t, NOW)
        e = roots.get(t.key)
        ctx = e.context if e else None
        nodes.append(
            {
                "id": t.key,
                "team": t.key.split("-")[0],
                "summary": t.summary,
                "owner": t.owner.name,
                "owner_tz": t.owner.timezone,
                "status": t.status,
                "dep_type": t.dep_type.value,
                "stale": s.is_stale,
                "days_stale": round(s.business_days_stale, 1),
                "is_root": e is not None,
                "in_blast": t.key in blast_union,
                "severity": ctx.severity.level.value if ctx else None,
                "severity_score": ctx.severity.score if ctx else None,
                "days_to_milestone": (
                    round(ctx.days_to_milestone, 1)
                    if ctx and ctx.days_to_milestone is not None
                    else None
                ),
                "milestone": t.milestone,
                "message": e.message if e else None,
            }
        )

    edges = [{"from": u, "to": t.key} for t in tickets for u in t.blocked_by]
    data = {
        "generated_at": NOW.isoformat(),
        "root_keys": list(roots),
        "blast_count": len(blast_union),
        "nodes": nodes,
        "edges": edges,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        "window.GRAPH_DATA = " + json.dumps(data, indent=2) + ";\n", encoding="utf-8"
    )
    print(
        f"Wrote {OUT}  ({len(nodes)} nodes, {len(edges)} edges, "
        f"{len(roots)} root(s), {len(blast_union)} in blast radius)."
    )


if __name__ == "__main__":
    build()
