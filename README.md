# Dependency Deadlock Detector

> Squad Alpha · NEU Tech Immersion Workshop FY26

An AI agent that watches everything a delivery team is waiting on, detects when
a dependency has gone **silent too long**, scores its **downstream blast
radius**, and **auto-drafts an escalation** to the right owner — before the
sprint collapses.

The core insight: *humans react to noise, not to the absence of activity.* This
tool notices the silence.

## Run the demo (no cloud, no credentials)

```bash
pip install -r requirements.txt        # on Windows, this installs tzdata (needed for timezones)
python run_demo.py
```

You'll see the slide's flow run end-to-end against mock Jira data:

```
silent ticket (4 working days) -> 3-node chain stalled -> 7 tickets blocked
-> sprint at risk -> escalation drafted -> sprint saved
```

Without Foundry credentials the drafter falls back to a $0 template, so the
demo always runs. Add credentials (below) and the same code uses Claude.

## How it works

```
ingest (Jira links) -> in-memory graph -> staleness -> blast-radius BFS -> severity
        │                                                                      │
        │                                              Drafter (Claude on Azure Foundry → template fallback)
        │                                                                      │
   dedupe (escalate once)  ───────────────────────────────────────►  Notifier (Jira comment → email → Teams)
```

- **~80% deterministic code, zero LLM tokens:** staleness detection,
  blast-radius BFS, severity scoring, dedupe. Reliable and free.
- **The LLM (Claude) touches exactly one step:** drafting the escalation
  message, once per *new* escalation. The model never counts tickets or
  traverses the graph.

### Staleness is smart, not naive

A fixed "48h" is the biggest product risk — it fires on weekends and ignores
timezones (India team vs Mexico team), producing false positives and alert
fatigue. Instead we measure **working hours the *owner* has had to act**, in the
owner's IANA timezone, skipping weekends + regional holidays. Thresholds are
per dependency type, in working days (client sign-off is looser than an internal
blocker). Weekends fall out for free: Fri 18:00 → Mon 09:00 = 0 business hours.

### Severity ranks, staleness only detects

`severity = f(downstream blast radius × proximity to milestone)` — not just age.

## "Claude via Azure" = Microsoft Foundry (not Azure OpenAI)

Azure OpenAI serves GPT models only; Claude lives in **Azure AI Foundry
(Microsoft Foundry)**, GA via serverless deployment (East US2 / Sweden Central),
**no separate access-request gate**. We use the dedicated `AnthropicFoundry`
client behind a `Drafter` interface. Selling point: the AI never leaves your
Azure tenant — same security and billing perimeter as the rest of your cloud.

To enable it: deploy a Claude model in your Foundry resource, then set
`AZURE_FOUNDRY_API_KEY` and `AZURE_FOUNDRY_RESOURCE` (see `.env.example`).
`FOUNDRY_CLAUDE_MODEL` defaults to `claude-haiku-4-5` (cost-optimal for short
drafting); set it to `claude-opus-4-8` for maximum quality.

## Layout

```
deadlock_detector/
  models.py         dataclasses: Ticket, Owner, DependencyType
  calendars.py      timezone/holiday-aware working calendar
  staleness.py      stage 2 — flag silent dependencies
  graph.py          stage 1 + 3 — adjacency + blast-radius BFS
  severity.py       stage 4 — blast radius × milestone proximity
  dedupe.py         escalate once; re-draft only if severity rises
  pipeline.py       orchestrates all stages
  ingest/           Ingestor interface + MockJiraIngestor (real Jira later)
  drafter/          Drafter interface + Claude-on-Foundry + template fallback
  notifier/         Notifier interface + console (demo) + Jira comment (prod)
data/mock_jira.json the demo scenario
run_demo.py         end-to-end demo
tests/              graph + staleness unit tests
```

## Tests

```bash
pytest
```

## Status / next steps

- [x] Portable deterministic core + mock-data demo running locally
- [ ] Wire `ClaudeFoundryDrafter` to a real Foundry deployment
- [ ] Implement `JiraCommentNotifier` against the Jira REST API
- [ ] Read-only blast-radius graph viz for the demo ("the wow")
- [ ] Azure Functions Timer-trigger wrapper (thin — calls this core)
