# 31 — Sweep detectors + raise_issue escalation (formerly PKT-16)
size ~0.25 wu · wave F (parallel-safe) · depends: v1.0
law: DESIGN-LAW §1.4 (misses/verdicts honesty) · spec: MASTER-PLAN §3 · DEPLOY: yes

## Mission
Close the discover→act loop the external review flagged (gap 4): sweep detectors
auto-populate findings, and `raise_issue` escalates a finding to the tracker with the
audit trail dead-reckoning lacked. `raise_issue` was explicitly deferred out of P8b to
P9 — this is that debt.

## Scope IN
- Detectors, opt-in per kind in lore.yaml: **dead_code** (existing analysis),
  **undocumented** (chunk metadata; packet 30's seeding path if it landed), **drift**
  (symbol changed while memories/findings reference it — snapshot diff makes it cheap).
- `lore_findings action=raise_issue`: gh CLI or Gitea API per
  `actions: {tracker, repo, …}` config; issue_url stamped back on the finding.
- Sweep-detector findings carry created_by=sweep; agent-filed stay as today.

## Scope OUT
- trace_monitor auto-filing (packet 35 — it needs the deepened traces).
- Any new tool (the action rides lore_findings).

## Entry check
Config seam for `actions:` exists or is added at the validated boundary; a throwaway
Gitea/GitHub repo available for the escalation smoke (never a real tracker).

## Exit
Full gates + cold audit; deploy BOTH; smoke: a sweep files a dead_code finding →
raise_issue lands a tracker issue → issue_url stamped back; INDEX row + Log.
