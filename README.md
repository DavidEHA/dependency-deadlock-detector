# Dependency Deadlock Detector

> Squad Alpha · NEU Tech Immersion Workshop FY26

An AI agent that watches everything a delivery team is waiting on, detects when
a dependency has gone **silent too long**, scores its **downstream blast
radius**, and **auto-drafts an escalation** to the right owner — before the
sprint collapses.

The core insight: *humans react to noise, not to the absence of activity.* This
tool notices the silence.

## Repo layout

```
backend/    Python agent — the deterministic pipeline + the LLM drafting step
frontend/   React + Vite + React Flow — the read-only blast-radius visualization
```

The contract between them is one JSON file: the backend writes
`frontend/src/data/graph_data.json`; the frontend renders it. The frontend
recomputes nothing.

## Backend — run the agent (no cloud, no credentials)

```bash
cd backend
pip install -r requirements.txt        # on Windows this installs tzdata (needed for timezones)
python run_demo.py                      # prints the slide flow end-to-end on mock Jira data
python export_graph.py                  # writes frontend/src/data/graph_data.json
pytest                                  # 6 tests (graph + timezone-aware staleness)
```

`run_demo.py` reproduces the slide:

```
silent ticket (4 working days) -> 3-node chain stalled -> 7 tickets blocked
-> sprint at risk -> escalation drafted -> sprint saved
```

Without Foundry credentials the drafter falls back to a $0 template, so it
always runs. Add credentials (below) and the same code uses Claude.

## Frontend — run the visualization

```bash
cd frontend
npm install
npm run dev            # open the printed localhost URL
```

(Re-run `backend/export_graph.py` whenever you change the scenario, then refresh.)

## How it works

```
ingest (Jira links) -> in-memory graph -> staleness -> blast-radius BFS -> severity
        │                                                                      │
        │                                  Drafter (Claude on Azure Foundry → template fallback)
        │                                                                      │
   dedupe (escalate once)  ──────────────────────────────────────►  Notifier (Jira comment → email → Teams)
```

- **~80% deterministic code, zero LLM tokens:** staleness, blast-radius BFS,
  severity, dedupe. Reliable and free.
- **The LLM (Claude) touches exactly one step:** drafting the escalation
  message, once per *new* escalation. It never counts tickets or walks the graph.

### Staleness is smart, not naive

A fixed "48h" is the biggest product risk — it fires on weekends and ignores
timezones (India team vs Mexico team), producing false positives and alert
fatigue. Instead we measure **working hours the *owner* has had to act**, in the
owner's IANA timezone, skipping weekends + regional holidays. Thresholds are per
dependency type, in working days. Weekends fall out for free: Fri 18:00 →
Mon 09:00 = 0 business hours.

### Severity ranks, staleness only detects

`severity = f(downstream blast radius × proximity to milestone)` — not just age.

## "Claude via Azure" = Microsoft Foundry (not Azure OpenAI)

Azure OpenAI serves GPT only; Claude lives in **Azure AI Foundry (Microsoft
Foundry)**, GA via serverless deployment (East US2 / Sweden Central), **no
separate access-request gate**. We use the dedicated `AnthropicFoundry` client
behind a `Drafter` interface. Selling point: the AI never leaves your Azure
tenant — same security and billing perimeter as the rest of your cloud.

Enable it: deploy a Claude model in your Foundry resource, then set
`AZURE_FOUNDRY_API_KEY` and `AZURE_FOUNDRY_RESOURCE` in `backend/.env`
(see `backend/.env.example`). `FOUNDRY_CLAUDE_MODEL` defaults to
`claude-haiku-4-5` (cost-optimal for short drafting); set `claude-opus-4-8`
for maximum quality.

## Status / next steps

- [x] Deterministic core + mock-data demo (`backend`)
- [x] React + React Flow blast-radius viz (`frontend`)
- [ ] Wire `ClaudeFoundryDrafter` to a real Foundry deployment
- [ ] Implement `JiraCommentNotifier` against the Jira REST API
- [ ] Azure Functions Timer-trigger wrapper (thin — calls the backend core)
```
