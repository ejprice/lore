# REPORT-ccguide-notify — Claude Code teammate idle/stop notification mechanics

Task: authoritative, doc-cited answer on whether/how hooks can suppress, rewrite, make
terse, or coalesce the teammate idle/stop notification the LEAD receives. Full answer was
delivered to team-lead in chat; this file is the receipt.

## Governing fact
Teammate -> lead idle/stop notification is TEAM-MAILBOX AUTO-DELIVERY, not a
hook-interceptable event on the lead side. No documented hook fires in the LEAD's session
when a team-internal message arrives.
(agent-teams.md #architecture, #context-and-communication)

## Q1 — Suppress/rewrite what the LEAD's model receives? NO. [DOCUMENTED]
- TeammateIdle fires in the TEAMMATE session; exit 2 / {"continue":false} govern the
  teammate (keep working / stop), NOT the lead's view.
- Notification: "No decision control ... side effects"; exit 2 "Shows stderr to user only" —
  cannot suppress/rewrite.
- MessageDisplay.displayContent: "Display-only: the transcript and what Claude sees keep the
  original" — reskins human terminal only, not the lead model context.
- suppressOutput hides the HOOK's own stdout only.
- additionalContext only ADDS, never removes/rewrites.
- CORRECTION: verbatim table does NOT say SubagentStop injects additionalContext into the
  PARENT/lead — that is INFERRED/unsupported. Whether an in-process teammate fires
  SubagentStop at all is UNDOCUMENTED (teams != subagents; teammates get TeammateIdle).
(hooks.md #decision-control, exit-code-2 table, universal fields)

## Q2 — Content/verbosity of the idle notification [MIXED]
- Harness-generated + auto-delivered, not the teammate transcript. Exact template
  UNDOCUMENTED. v2.1.198+: API-error termination notifies lead "and includes the error text".
- No knob to make the harness idle-notification terse; you control the teammate's OWN
  SendMessage text (plain text it authors) + REPORT file for detail.

## Q3 — Coalesce / reduce frequency [DOCUMENTED lever, at the SOURCE]
- No setting throttles teammate->lead idle notifications. crossSessionInbound +
  cross-session dedupe are for INDEPENDENT sessions; "structured agent team protocol messages
  stay within a team".
- Documented lever: TeammateIdle exit 2 "Prevents the teammate from going idle, so it
  continues working" — gate idleness on REPORT-<name>.md so idle (-> lead notify) fires only
  once genuinely done. This is exactly the repo's teammate-idle-gate.sh.

## Q4 — One terse, disambiguated signal per completion [compose it; no dedicated feature]
1. TeammateIdle exit-2 gate on completion artifact (existing hook).
2. Teammate sends ONE terse SendMessage summary + REPORT-<name>.md for detail-on-demand.
3. Disambiguation only partially harness-handled (v2.1.198 failure vs finish); full #67165
   ambiguity resolved via artifact + process-table ground-truth.

## Version / doc-status flags
- Agent teams EXPERIMENTAL, gated on CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1, doc "as of
  v2.1.178". team_name in TeammateIdle/TaskCreated/TaskCompleted payloads is DEPRECATED.
- TeammateIdle/TaskCreated/TaskCompleted OUTPUT contracts documented; INPUT payloads thin.
- Stop/SubagentStop/Notification contracts authoritative for THEIR events but do NOT govern
  teammate->lead mailbox delivery (no documented lead-side interception hook).

Sources: https://code.claude.com/docs/en/hooks.md ,
https://code.claude.com/docs/en/agent-teams.md ,
https://code.claude.com/docs/en/cross-session-messaging.md
