# Dependency Deadlock Detector — Project Brief

> Squad Alpha · NEU Tech Immersion Workshop FY26
> Brief captured from the design conversation. Use as the starting context for a fresh working session in this folder.

## One line
An AI agent that watches everything a delivery team is waiting on, detects when a dependency has gone silent too long, scores its downstream blast radius, and auto-drafts an escalation to the right owner — before the sprint collapses.

---

## The problem
Blockers get raised in Jira once, then silently age. Cross-team and client dependencies stall unnoticed (buried in a board of 200 tickets) until a milestone is already missed. Core insight: **humans react to noise, not to the absence of activity** — nobody notices silence.

## What it does (4 steps)
1. **Build a live dependency graph** — map everything the team is blocked on across workstreams.
2. **Monitor for staleness** — flag any dependency node with no activity beyond a threshold.
3. **Score downstream impact** — count how many tickets / workstreams / milestones are blocked by that one stalled node; assign a severity score.
4. **Auto-escalate** — draft a context-rich nudge (chain + impact + suggested fix) to the right owner; a human approves and sends.

---

## Key design decisions (from the review)

### Scope the MVP narrow
- **Ingest Jira issue links only** (`blocks` / `is blocked by` + status + last-updated). Structured and reliable.
- **Defer emails / meeting transcripts to phase 2** (LLM extraction is noisy — don't let it eat the demo).

### Split the work correctly: code vs LLM
- **Deterministic code** (zero tokens): staleness detection, blast-radius BFS, severity scoring.
- **LLM (Claude) only for language tasks**: drafting the escalation message (MVP); extracting deps from unstructured text (phase 2).
- Never make the LLM count tickets / traverse the graph — unreliable and costly.

### Make staleness smart, not naive
- A fixed "48h" is the **biggest product risk** → false positives → alert fatigue → people ignore it (the exact failure it's meant to fix).
- Make it **business-hours aware** + **per-dependency-type thresholds**.
- **Severity = f(downstream blast radius × proximity to milestone)**, not just age.

### Dedupe is mandatory (cost + trust)
- The hourly scan must **escalate a node only once** (mark "already escalated"; re-draft only if severity rises).
- Without dedupe: re-calls the LLM every hour on the same stale node = wasted tokens **and** spams the owner.

### Drop Neo4j for the MVP
- A team's dependency graph is small (hundreds of nodes). An **in-memory adjacency + BFS** computes blast radius instantly. Add a graph DB only if scale ever demands it.

### It's mostly a pipeline, and that's good
- ~80% is a deterministic pipeline (ingest → graph → threshold → score → notify) with the LLM at 1–2 steps — more reliable than a fully autonomous agent.
- **Multi-agent is optional flair**: if desired, split an *Extractor* agent (text → deps) and an *Escalation drafter* agent. Don't invent 5 agents where a pipeline + 2 LLM calls suffice.

---

## UI — is it necessary?
- **Product: no standalone UI needed.** The only human touchpoint is "approve & send", which lives where the team already works.
- **Demo: a small read-only graph visualization is worth it** (the "wow" — blast radius lighting up red). Feed it the agent's JSON; demo-only.

## Delivery channel & the permissions reality
- **Corporate Teams admin is locked** for this account (`INVALID_PRIVILEGE` on Teams Admin Center). Corporate Azure is likely equally restricted.
- The Teams "Adaptive Card with Approve button" is the prettiest path but the **most permission-gated** (Entra app registration + admin consent + app sideload).
- **Lower-friction Teams paths:** Incoming Webhook (being deprecated) → **Power Automate "Workflows"** (uses your own permissions, often allowed). Test by trying to create one on a test channel.
- **Best no-permission path for production: escalate as a Jira comment with an @mention** on the stalled ticket (and optionally a linked escalation task). Uses Jira access you already have — zero new approvals.
- **Design rule: make delivery channel-agnostic** — a pluggable `Notifier`. Jira-comment primary (no gate); email basic; Teams optional once IT consents.
- **For a full Teams demo:** spin up your own **M365 Developer / Entra tenant** (you're admin → full Teams + Graph). Caveat: a personal tenant is isolated — it proves the mechanism but does **not** grant access to the corporate Teams; production still needs corp consent. Use the working demo as the artifact that *earns* that approval.

---

## LLM API consumption
- The LLM is called **once per new escalation only** (not per scan). Real escalations are a handful per day.
- Rough size: ~2k tokens in + ~0.5k out per escalation → **fractions of a cent each** with a cheap model (Haiku-class). Negligible for MVP/demo; covered by trial credits. (Verify current prices.)
- **Dedupe keeps it cheap** (see above).
- Abstract the call behind a `Drafter` interface:
  - Dev/demo free: **Gemini** (real free tier) or **Claude** trial credits.
  - Production: approved provider (Claude direct / Azure OpenAI).
  - `$0` fallback: a fixed **template** (no LLM); LLM only raises message quality.

## Free / trial options (to cover inference)
| Provider | Offer | Note |
|---|---|---|
| Google AI Studio (Gemini) | Genuine free tier | Most "free for real" for dev/demo |
| Anthropic (Claude) | Initial trial credits | Familiar; pay-per-token after |
| AWS | New-account credits (~$100–200) | Spend on Bedrock (Claude/Nova) |
| Google Cloud | $300 / 90 days | Vertex AI (Gemini) |
| Azure | $200 / 30 days + 12-mo free | Functions + Azure OpenAI (access-gated) |

> Free-tier amounts/terms change often and vary by region — verify before committing.

---

## Recommended MVP architecture (cloud-agnostic core)
```
core (portable, no cloud lock-in):
  ingest Jira links → in-memory graph → staleness + BFS blast radius → severity
        │                                                              │
        │                                                   Drafter (Claude → template fallback)
        │                                                              │
  Scheduler (interface)  ── local first; Azure Functions = optional adapter
  Notifier  (interface)  ── email basic; Jira-comment (no gate); Teams optional
```
- **Do not couple the MVP to Azure.** Azure's only structural role is a scheduled trigger (cron) — replaceable by a local script, `setInterval`, or a free GitHub Actions schedule. Azure Functions is just one deploy target.
- Keep the core runnable locally today; "deploy to Azure Functions" is a thin wrapper.

## Demo flow (matches the slide)
Silent ticket (4 days) → 3-node chain stalled → 7 tickets blocked → sprint at risk → **Claude drafts escalation** → approve → "sprint saved".

---

## Azure deploy steps (optional adapter — run with YOUR Azure account)
> Likely a **personal/free** Azure account (corporate is probably locked). Yo can scaffold the Function code; you run the cloud commands.

1. **Verify access** — try creating a Resource Group in the portal; if denied, use a personal free account.
2. **Tooling:** `winget install Microsoft.AzureCLI` + `Microsoft.Azure.FunctionsCoreTools`; then `az login`; `az account set --subscription <sub>`.
3. **Resources:**
   ```bash
   az group create -n rg-deadlock-detector -l eastus
   az storage account create -n stdeadlock<rand> -g rg-deadlock-detector -l eastus --sku Standard_LRS
   az functionapp create -n func-deadlock-detector -g rg-deadlock-detector \
     --storage-account stdeadlock<rand> --consumption-plan-location eastus \
     --runtime node --functions-version 4
   ```
4. **Secrets via app settings** (Jira token, LLM key, SMTP) — or Key Vault for prod.
5. **Function code:** `func init` + `func new --template "Timer trigger"` → the trigger just calls the portable core (don't reimplement logic).
6. **Deploy:** `func azure functionapp publish func-deadlock-detector`. Verify via Application Insights / Log stream.

### Gates to sidestep
- **Azure OpenAI needs a separate access request** → call **Claude/Gemini directly** from the Function instead.
- **Azure email (ACS) needs a verified domain** → use plain **SMTP** (org SMTP or a free tier like Resend/SendGrid) for "something basic".

---

## Open decisions / next steps
- [ ] **Stack:** Node/TS (frontend dev's comfort zone) vs Python.
- [ ] **Primary delivery for production:** confirm Jira-comment/@mention (no permission gate).
- [ ] **LLM provider for dev:** Gemini free tier vs Claude trial credits.
- [ ] **Repo home:** this folder (`dependency-deadlock-detector`), its own `git init`, separate from the KM (Accenture) repo. Push to GitHub manually (`gh` not available in the current env; create the empty repo then `git remote add` + `git push`).
- [ ] Scaffold: portable core + `Scheduler`/`Notifier`/`Drafter` interfaces + email sink + Timer-trigger wrapper.

> Suggested: continue in a **new Claude Code session opened in this folder** so workspace, git and permissions are scoped to this project (not the KM repo).
