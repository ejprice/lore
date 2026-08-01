# REPORT-design-agentfix-1 — ruling on the agent-comms fix (A1–A5)

brief-base v9 read
state: done
deviations: minimal file reads performed (brief-base as required; frontmatter of `tdd-contract.md`, `odoo-consumer-scout.md`, `security-auditor.md`; two greps) — the brief demanded exact frontmatter, and one inherited count needed re-derivation. Report file written per brief-base §1 even though the spawn brief names the message as the deliverable.
Packages considered: none — no mechanism specified (rulings over harness-native agent config; no library surface in play).
decisions-needed: none — operator delegated decision authority verbatim; the one item deliberately deferred to the operator (server rename) carries a named decision point, below.
receipt pointers: evidence base = `docs/plans/v2/receipts/2026-08-01-agent-comms-fix/` (`d5ea7b0`); measured corrections in §A2 and §Corrections below.

These are DECISIONS, not recommendations, issued 2026-08-01 under the operator's verbatim
delegation. Scope: the five questions in the spawn brief, nothing else.

---

## A1 — THE FIX FORM: delete the `tools:` block. Entirely.

**Ruling:** the seven lore-needing definitions (`tdd-contract`, `tdd-implementer`,
`tdd-stub`, `tdd-refactorer`, `tdd-light-contract`, `contract-adversary`,
`package-scout`) each lose the whole `tools:` key, including its comment lines. Exact
frontmatter for `tdd-contract` (same transform for the other six — every other existing
key is kept byte-for-byte, `tools:` and its comments are removed, nothing is added):

```yaml
---
name: tdd-contract
description: "Writes contract tests. No knowledge of implementation."
---
```

**Why this shape and not the other three** (dated 2026-08-01; grounds measured this session
at `d5ea7b0`):
- It is the only shape **execution-proven for user-defined definitions** that restores lore
  in EVERY project with no per-project name: the unrestricted shape is proven live
  (`general-purpose`/`claude`), and `~/.claude/agents/security-auditor.md` — the same
  artifact class as the files being edited — already ships with **no `tools:` key** and
  renders as "All tools".
- **Exclusion list: rejected for the blocking path.** It is measured only on built-ins
  (`Explore`, `Plan`); no execution proof exists that user-definition frontmatter has an
  exclusion grammar at all. Ruling it would be the #266 defect re-committed: a remedy
  adopted and documented without measurement. It may be probed later, unblocked (see the
  re-tighten trigger below).
- **Literal `mcp__lore_lore__*` names: rejected as the global fix.** Correct for exactly
  this project, silently wrong in every other, and the wrongness is byte-identical to the
  bug being fixed. It becomes the RIGHT shape only after the server-name unification
  (§A5, filed follow-up) — the existence proof is already in production: the odoo scouts'
  literal allowlist works *because* `odoo-code` is a project-invariant server name.
- **Project-local `.claude/agents/` clones: rejected.** Nine copies of policy per project
  is the §ONE IMPLEMENTATION violation by construction.

**What deletion actually grants, judged honestly:** the tdd isolation that matters is
informational — the contract author must not *read* the implementation — and that is
enforced by brief content, not grants (`tdd-contract` already holds Write+Bash; nothing in
an allowlist ever enforced the isolation). The one real delta is `Agent` (nested
spawning). **Accepted**: teammates structurally cannot spawn teammates, the subagent
system prompt forbids re-delegating the assignment, and withholding-by-enumeration is the
instrument-lesson losing game. Re-open trigger, named: the first observed harmful nested
spawn inside a tdd wave, OR the fixed-name rename landing — either reopens the question of
re-tightening with literal `mcp__lore__*` allowlists. Until a trigger fires, unrestricted
is the standing shape.

**Rider (in this bullet, per repo law):** the fix is proven per-file by §A4's execution
receipts — seven edited artifacts, seven independent live-call receipts, no extrapolation
from one file to another. No new prose claim about reachable tools is added to any
definition: a definition cannot know its session's grants, so it teaches nothing about
them (the truth lives in the corrected load lines and the new finding, §A5).

## A2 — SCOPE: seven change, two stand, the false comment dies everywhere it lives.

- **Change (delete `tools:`):** `tdd-contract`, `tdd-implementer`, `tdd-stub`,
  `tdd-refactorer`, `tdd-light-contract`, `contract-adversary`, `package-scout`.
- **Unchanged:** `odoo-consumer-scout`, `odoo-reuse-scout`. Their allowlist is
  execution-proven working for their entire needed surface, and the Odoo tree is not on
  lore — a `mcp__lore_lore__*` grant would name a server their working project doesn't
  run. Re-open trigger, named: **the day a `lore.yaml` lands in the Odoo tree**, their
  grants are revisited (by then the rename follow-up should make it a portable
  `mcp__lore__*` one-liner). `security-auditor` is not in the nine and is untouched.
- **The false #266 comment:** measured this session — it lives in **SIX** files, not the
  brief's seven (`grep -n "266" ~/.claude/agents/*.md`: the five tdd files +
  `package-scout`; `contract-adversary` carries no hit). Ruling: it dies with the deleted
  `tools:` blocks, and **nothing replaces it in the agent files** — the corrected teaching
  lives in the skills' load lines (§A5) and the new finding. Rider: the fix report pastes
  a post-fix anchor-free grep over `~/.claude/agents/` and `~/.claude/skills/` for `266`
  and for `gateway to deferred` showing **zero hits**, every residual hit (if any)
  file:line'd with an individual verdict per the sweep law.
- **`Grep`/`Glob` listed-but-undelivered:** structurally moot — all seven listing files
  lose their allowlists, so the false grants vanish with them. The FACT ("an allowlist
  entry is a request, not a possession; only execution is evidence") is recorded in the
  new finding's body (§A5), not in any definition's prose.

## A3 — THE INSTRUMENT: a possession receipt at every use; the rest is a PINNED MISS.

- **The enforceable half — a per-use execution receipt, wired into the skill briefs.**
  Add to the spawn-brief templates in `~/.claude/skills/tdd/SKILL.md` and
  `~/.claude/skills/tdd-light/SKILL.md` (every phase that spawns an agent): numbered
  first steps = the corrected ToolSearch load line (§A5) → **call `lore_index()`** → the
  report's summary block carries `lore: lore_index ok @<last_sync stamp>` or
  `lore: UNREACHABLE — <what ToolSearch actually returned>`. Lead-side semantics, same as
  a missing brief-base receipt: **a missing or failed lore line ⇒ the agent is treated as
  ungranted and the wave STOPS.** Why this is an instrument and not a hope: it is a
  checked expectation at a checkpoint the lead already reads (the summary block), it
  counts only execution (probe 4: listed ≠ callable), and it is the dogfood protocol's
  mandated freshness-first step doing double duty — the check runs because the work
  cannot legitimately start without it. It also converts every future project's FIRST
  tdd spawn into that project's acceptance test, which closes §A4's cross-project bound
  loudly instead of silently.
- **The dead-name half:** `scripts/lore_tool_name_currency.py` is committed; wire ONE
  checklist line into the `lore-deploy` skill's `start` verb: run the scan, non-zero ⇒
  file friction. Honest label: that line is a procedure, the weakest instrument here —
  the per-use receipt above is the hard one.
- **The remainder cannot be closed, and is PINNED as a miss** per repo law: no repo
  pytest can see `~/.claude/agents/`, and a home-dir-asserting test is its own defect.
  The pin lives in the LEDGER, not in pytest — the new finding (§A5) records it in
  KNOWN-BOUND form with named re-open triggers: (a) the harness gains project-layered
  agent config (override without cloning), (b) the harness exposes a tool-grant
  introspection surface a script can read, (c) the fixed-name rename lands, making
  literal grants portable and mechanically greppable. Until one fires, the grant half is
  guarded at use-time only, and the finding says so in those words.

## A4 — THE ACCEPTANCE BAR: seven spawns, live calls, and the server's own roster as the receipt.

- **The test:** after the edits, spawn ALL SEVEN changed types in parallel (one message).
  Each micro-brief: read brief-base (receipt line) → `ToolSearch
  "select:mcp__lore_lore__lore_index,mcp__lore_lore__lore_comms"` → **CALL**
  `lore_index()`, then `lore_comms action=register`, then `lore_comms action=drain` —
  the exact verb family the operator named broken — and paste each rendered output
  verbatim in its report. Seven files are seven independent artifacts; each gets its own
  receipt, no extrapolation.
- **The strongest receipt is server-side, not agent-side:** the lead then calls
  `lore_comms action=fleet` itself and confirms **all seven registrations appear** —
  the recipient's own artifact, per standing comms law. The lead also calls
  `lore_index()` itself and cross-checks the `last_sync` stamp against each agent's
  pasted render (a fabricated render cannot match a live stamp).
- **Negative control:** already exists, same-session, committed — packet 39's four
  reproductions plus this session's probes at `d5ea7b0` show the pre-fix shape failing
  under the identical session config. No new pre-fix spawn is spent on it.
- **NOT proven if any of:** a report claims presence via listing (ToolSearch match,
  `tools/list`) without a successful CALL and pasted render · any of the seven is missing
  from the lead's own fleet read · a stamp mismatch · fewer than seven agents receipted.
- **The stated bound (say it in the close-out, verbatim scope):** this proves "the seven
  definitions reach THIS project's `mcp__lore_lore__*` server, this session." Portability
  to other slugs is BELIEVED — mechanism: no name is hardcoded, so there is nothing to be
  wrong — not KNOWN. The §A3 receipt protocol is the instrument that makes each other
  project's first spawn its own acceptance test, so the bound closes at first use, loudly.

## A5 — THE DEAD NAMES: fix all four files now; one superseding finding; rename filed, not executed.

- **Fix all four files** (`~/.claude/CLAUDE.md`, `skills/tdd/SKILL.md`,
  `skills/tdd-light/SKILL.md`, `skills/odoo-dev/SKILL.md`), not just the two the operator
  named. Grounds: the `~/.claude/CLAUDE.md:344` canonical load line is the compounding
  half of the outage — a correctly-granted agent pasting it loads almost nothing — so
  fixing agents without it ships the bug's second half; and `odoo-dev`'s nine
  "hypothetical" hits are the MOST dangerous kind — retired names that nothing will ever
  execute to falsify, taught to the exact future session that onboards Odoo to lore.
  Leaving known hits also permanently poisons the committed scan (a gate that always
  cries becomes a gate that gets switched off).
- **The canonical load line's replacement** (mapping from the live `tools/list` in the
  receipts): `lore_search_code`→`lore_search`; `lore_what_imports`→`lore_impact`;
  `lore_tests_for`→`lore_impact` (covering-tests view). New line:
  `ToolSearch "select:mcp__lore_<slug>__lore_search,mcp__lore_<slug>__lore_get_symbol,mcp__lore_<slug>__lore_impact,mcp__lore_<slug>__lore_index"`
  — orchestration briefs append `...lore_comms,...lore_findings` as their tasks require.
  The remaining ~31 dead names map mechanically from the same live inventory.
- **Rider (the gate for this bullet):** `scripts/lore_tool_name_currency.py` output
  showing **0 dead names across all four files**, pasted in the fix report — PLUS an
  anchor-free grep for the three headline dead names across all of `~/.claude/`
  (bare patterns, per sweep law), because the scanner's four-file scope is a hand-list
  until the grep confirms it missed nothing; every residual hit gets file:line + verdict.
- **Ledger disposition:** #292's "append here" instruction is unexecutable — no body-edit
  verb exists (#129) — so: file **ONE fresh finding** carrying the full measured
  taxonomy (three shapes), the fix form, the A3 known-bound + its three triggers, and the
  allowlist-is-a-request fact; its body OPENS with "Supersedes #292 and #294 (append
  impossible: no body-edit verb — see #129; this filing pattern is the workaround)".
  Then **resolve #292 and #294** with resolution notes naming the new finding's id and
  `docs/plans/v2/receipts/2026-08-01-agent-comms-fix/`. The class stays one row — the new
  row IS the row, and its own re-open instruction says "supersede-and-resolve again,
  citing this row" rather than repeating #292's impossible verb.
- **The server rename to a fixed `lore`: ADOPTED in principle, FILED, not this session's
  work.** It is the allowlist-the-safe-set shape — it converts an unbounded per-project
  name into a fixed one, per-project `.mcp.json` scoping makes collisions impossible, and
  `odoo-code` is the working existence proof. But MCP config binds at session start, so a
  mid-session rename is invisible to this session and **cannot even be acceptance-tested
  now**; and it touches every project's `.mcp.json`, the `lore-deploy` skill, and every
  doc naming `mcp__lore_<slug>__*`. File it as a ledger item with the named decision
  point: **operator ratifies on return; `lore-deploy` skill packet implements; until it
  lands, the seven definitions stay unrestricted** (re-tightening with literal names is
  only coherent after the rename).

## Corrections to inherited numbers (re-derived this session, 2026-08-01)
- False-comment sites: **6 files**, not 7 (`contract-adversary` carries no `#266` hit).
- `security-auditor.md`: no `tools:` key + pinned `model: opus` → harness renders
  "All tools" — corroboration that deletion is the correct user-definition syntax.
