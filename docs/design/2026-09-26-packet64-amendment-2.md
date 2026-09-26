# Packet 64 — ruling amendment 2 (sidecar-64, 2026-09-26): OF-2 = RETIRE AT 65 — `created_by` / `actor` / `owner` become foreign-param refusals on `lore_tasks`, `lore_findings`, `lore_claim_task`

Amends `docs/design/2026-09-26-packet64-kickoff-rulings.md` (`e5fa7f9`) §6 (F5), §12 (the F5 row), §14
(items 1–6), §16 (the F5 rider); confirms §12 as amended by amendments 1 and 2 for the 64b contract
author (§7 below). Directive: `REPORT-lead-63c.md@f4511ef` (durable copy). **Operator ruling OF-2 =
RETIRE AT 65, overriding my recommendation** (optional-checked args): the three args become foreign-param
refusals at the 65 cutover, landing together with `capability=` required. HEAD at ruling: `f4511ef`.
Facts read this turn (`awk` over `server.py`/`tests/`/`CLAUDE.md`, said so; lore for the rest): the MCP
layer refuses an argument outside a tool's schema with pydantic's `extra inputs are not permitted
[<field>]` (names the field, carries no remedy); the comms strict-param idiom is
`AppContext._comms_foreign_param_error` (*"'X' applies only to action=… — omit it for …"* — a teaching
refusal, but for a param that is LEGAL on a sibling action, which a retired param is not); 74 lines of
served prose in `server.py` name the three args; the standing comms brief `project` v7 teaches
*"needs category+area+created_by"*; both CLAUDE.md files carry the same sentence.

## 0. The ruling in one screen

| item | ruling |
|---|---|
| **Surface** | The three parameters are REMOVED from the served schema of the three tools at their retrofit waves (`created_by` and `actor` from `lore_findings` in 64b; `created_by`/`actor`/`owner` from `lore_tasks` and `owner` from `lore_claim_task` in 64a). `lore_claim_task(task_id, *, capability, agent, session)`. A retired name is NOT advertised-but-refused: a schema that lists a parameter whose only behaviour is to refuse teaches the wrong contract by existence (agents learn the tool FROM the schema — the consumer law). |
| **The refusal** | A caller still passing one meets the MCP layer's own extra-input refusal, which NAMES the field. Teaching is layered where a read-once contract belongs (DESIGN-LAW §1.5): each tool's DESCRIPTION carries ONE shared retirement sentence with the remedy (§2); and the packet TRIES to attach that same sentence to the refusal itself through a FastMCP input-validation hook — the builder READS the installed FastMCP source for one (never assumes); present ⇒ the refusal text = field + the shared sentence; absent ⇒ an ACCEPTED BOUND, pinned, re-open *"the day FastMCP exposes a validation-error hook"*. Either way the served refusal names the field and ZERO rows are written. |
| **Display provenance** | Unchanged from kickoff §6: derived from the Subject's own agent row — `provenance.created_by` / `finding.created_by` / `events[].actor` / the CLAIMANT string `task.owner` := `own_row.name`, plus `events[].actor_agent` := the agent RecordID. The ledgers KEEP their `created_by=`/`actor=`/`owner` parameters (the tool passes the derived name; the ledger is not the composition root — 63-rulings §10.5). |
| **Which wave** | The refusal code (the schema removal + the description sentence + the derived-provenance plumbing) lands WITH each tool's retrofit wave — 64b for findings, 64a for tasks + claim — never as its own wave: it IS the F5 half of the retrofit. Nothing deploys before 65, so the tree carries the retired surface while the deployed image keeps serving the old one; the in-repo consumers are swept in the same waves; the fleet-facing re-brief is 65's (§5). |
| **The 65 landing** | At the cutover the retired args and `capability=` required arrive TOGETHER (one break, one re-brief): the deploy smoke drives a governed call with `created_by=` and asserts the field-naming refusal, and one without it that succeeds with derived provenance. |

## 1. F5 revised (replaces kickoff §6 items 2 and 4; items 1, 3, 5 stand)

1. Identity from `capability=` via the ONE composition root + the 63c dispatcher helper (`_resolve_identity`:
   Subject → own row by id → `agent=`/`session=` self-consistency check) — UNCHANGED.
2. **RETIRED:** `created_by`, `actor`, `owner` leave the three tools' signatures (hence their served
   schemas). No optional-check branch is built (kickoff §6 item 2 is WITHDRAWN before it was born). The
   identity-compare site (kickoff rider iv) compares ONLY `agent=`/`session=`.
3. Provenance strings populated from `own_row.name` (+ `actor_agent` id in events) — UNCHANGED.
4. `lore_claim_task(task_id, *, capability, agent, session)` — the claimant string := `own_row.name`.
5. `rollup`: `capability=` REQUIRED — UNCHANGED.
6. **The R8(2) footer fallback** (`attributions=`) is DELETED for the three tools — now trivially: no
   caller value exists to match; the third-person *"matched, never authenticated"* served line and the
   `agent=` description's *"one disclosed exception"* sentence go with it (P8d sweep, §4).

## 2. The refusal's teaching text (ONE shared constant; the consumer law's field · rule · remedy)

`_RETIRED_IDENTITY_ARGS_TEACHING` (one string, referenced by the three descriptions and, if the hook
exists, by the translated refusal):

> *"`created_by`, `actor` and `owner` were RETIRED at the 65 cutover: identity is DERIVED from the
> capability you present — pass `capability=` (the one-time secret `lore_comms action=register` returned;
> re-register under a fresh name if you no longer hold it) and drop the retired argument. Your registered
> agent name is recorded as the author/actor/claimant automatically."*

- Field: the pydantic refusal names it (`[created_by]`); with the hook, the translated text prefixes the
  sentence with *"`created_by=` is retired —"*. Rule: derived, not declared. Remedy: `capability=` + drop.
  No other agent, session or row is named (no oracle).
- The sentence lives ONCE (the `capability=` description-constant idiom, 63-rulings §10.5 rider i); a
  second spelling anywhere in `server.py` reds the prose pin (§4).
- The `lore_tasks`/`lore_findings`/`lore_claim_task` descriptions gain it as their LAST sentence; the
  `capability=` parameter description (shared) is unchanged.

## 3. Where display provenance comes from (restated so a retrieved chunk carries it)

| stored value | source after 65 | note |
|---|---|---|
| `task.provenance.created_by`, `finding.created_by` | `own_row.name` (the Subject's agent row, read by id in `_resolve_identity`) | #100's name convention; the LINK (`owner_agent`) is the truth |
| `provenance.events[].actor` | `own_row.name` | plus `events[].actor_agent` = `agent:<id>` (additive) |
| `task.owner` (the CLAIMANT) | `own_row.name` at claim | the CAS, `query owner=`, `resolve_holder` unchanged in shape (kickoff F2) |
| the pending-traffic footer's agent | the Subject's own row | the exact-match fallback is gone |
| audit rows (admin bypasses) | `subject.principal_id` / `subject.agent_id` | unchanged |

## 4. Riders revised — and pin it like this

- **F4 fuzz ∀ write verbs of both tools + claim (derived from the spec dicts):** the hostile set becomes
  `{owner_principal=, owner_agent=, as_agent=, created_by=, actor=, owner=, scope=<foreign keep>,
  scope=server}`. For each RETIRED name: the call is refused at the MCP layer, the refusal text CONTAINS
  the field name, ZERO governed mutations (F5 observer), and the same call without it succeeds with
  `provenance.created_by == own_row.name` (positive control). With the hook present, the refusal text
  also contains the shared teaching constant (asserted by identity, not by a second literal).
- **The schema pin (allowlist the safe):** the served input schema of each of the three tools is EXACTLY
  its post-retirement parameter set (a constant per tool in the pin — the 62 input-schema pin extended);
  a retired name reappearing reds; `capability=` present with the shared description.
- **The prose sweep (BARE, anchor-free, every hit a file:line + verdict):** `created_by`, `actor`,
  `owner=`, `never authenticated`, `disclosed exception` over `server.py` (descriptions + the derived
  instructions block), `CLAUDE.md`, `~/.claude/CLAUDE.md` (flagged to the operator — outside the repo),
  `docs/eval/smoke_p8b.py`, `docs/plans/v2/INDEX.md`'s 64/65 rows, and the `project` comms brief text.
  Verdicts at each wave close; the residual set at 64 close is the 65 re-brief list (§5). Ledger-level
  `created_by=` (`ledger.create_task(..., created_by=)` in `scripts/*.py` probes) is NOT retired — verdict
  `ledger-param, stands`.
- **The hook question is a MEASURED fact, not a belief:** the builder's report cites the installed FastMCP
  file/symbol that does or does not expose an input-validation error hook (`Packages considered:` row —
  `replace_with_adapter` if present, `keep_with_trigger` if absent). A `bespoke` refusal-translation that
  intercepts pydantic errors by TEXT is REJECTED (a literal-keyed instrument).
- **Deploy smoke (65):** one governed call per tool WITH a retired arg → the field-naming refusal; one
  without → success + derived provenance; recorded in the cutover receipts.

## 5. The 65 re-brief obligation — every brief, skill, habit and served surface that passes or teaches the args (derived by the §4 sweep at `f4511ef`; the sweep at 64 close is authoritative)

| surface | what changes | owner / when |
|---|---|---|
| the three tools' served descriptions + parameter schemas | retired names gone; the shared teaching sentence added; `capability=` shared description | 64b (findings), 64a (tasks, claim) |
| the derived `_INSTRUCTIONS` block (`build_instructions`) | its `lore_findings (kind=friction) files gaps` / `lore_tasks` lines mention no identity arg; teach `capability=` once | 64a/64b (whichever lands last owns the final text) |
| the comms standing brief `project` v7 (*"needs category+area+created_by"*) | `brief_publish` v8 at the cutover: *"needs category+area, and `capability=` (your register secret)"* | 65 (the fleet re-brief step, 63-rulings §2.6 step 5) |
| repo `CLAUDE.md` dogfood protocol line 4 (*"REQUIRES category, area, created_by"*) | rewrite to `capability=` | 64 close (repo doc; the lead's hand) |
| `~/.claude/CLAUDE.md` lore section (*"`action=report` needs category + area + created_by"*) | rewrite | OPERATOR (outside the repo — flagged, not edited by anyone here) |
| `docs/eval/smoke_p8b.py` (`actor=FINDING_ACK_ACTOR`) | pass `capability=`; drop `actor=` | 64b (the smoke is in-repo and runs at 65) |
| spawn-brief templates that say *"file it with `lore_findings action=report` (category, area, created_by)"* — `~/.claude/orchestration/brief-base.md` §4 names the project CLAUDE.md as the carrier (no literal hit); `lead-base.md` no hit; `~/.claude/agents/*.md` no hit; `~/.claude/skills/*/SKILL.md` no hit | none needed beyond CLAUDE.md; the sweep at 64 close re-confirms | 64 close |
| lore MEMORY notes recalled by agents that teach `created_by` (e.g. the packet-62/63 resume notes) | `lore_remember` ONE superseding note at 65: *"identity args retired; pass `capability=`"* — not a rewrite of history | 65 |
| every live fleet agent's habit (`lore_findings action=report … created_by=me`) | the 65 re-brief: every spawn brief carries `capability=` (62 W2.6's obligation, already 65's) — the retired args need no separate instruction beyond the description sentence: a stale habit meets a field-naming refusal + the description, once | 65 |

## 6. §14 removed-behaviour inventory — rows 1–6 replaced

1. `created_by=` REQUIRED on `create`/`create_many`/`supersede`/`report` → **RETIRED** (dropped-
   deliberately: OF-2; every `_require_arg(created_by)` / `_require_finding_arg(created_by)` refusal and
   every test asserting *"created_by is required"* is a DUAL row → DELETE-WITH-REPLACEMENT by the schema
   pin + the F4 retired-name leg).
2. `actor=` REQUIRED on transition/acknowledge/resolve/wontfix/annotate/the batches → **RETIRED** (same).
3. `owner` REQUIRED positional on `lore_claim_task` → **RETIRED**; the claimant string derived
   (preserved-with-pin: CAS / filter / `resolve_holder` shapes unchanged).
4. The kickoff's optional-CHECK branch for the three → **NEVER BORN** (withdrawn by OF-2 before build).
5. The R8(2) footer fallback + its two served sentences → DROPPED (as before).
6. `agent=`/`session=` on the three tools → SELF-CONSISTENCY CHECK (unchanged from kickoff §14 item 6).
7. **NEW:** the three tools' descriptions and `lore_claim_task`'s docstring (*"owner: free text …"*) →
   REWRITTEN with the shared teaching sentence (P8d prose class; the sweep is the instrument).

## 7. The 64b contract worklist (§12) — CONFIRMED as amended by amendments 1 and 2 (for the 64b contract author)

The kickoff §12 table stands with these deltas and nothing else:
- **F5 row → this amendment:** replace *"`created_by=`/`actor=` optional; supplied-mismatch ⇒ deny …"*
  with: `created_by`/`actor` ABSENT from `lore_findings`' schema (the exact-set schema pin); the F4 hostile
  set includes `created_by=`/`actor=`; a retired name ⇒ MCP-layer refusal naming the field, 0 writes;
  provenance := `own_row.name` + `events[].actor_agent`; the footer fallback gone (the `never
  authenticated` / `disclosed exception` sweep → 0 hits in the governed three); the shared teaching
  constant present once and referenced by the three descriptions (two land in 64a; the constant itself
  and the findings description in 64b); the hook question answered in the builder's `Packages
  considered:` row. The `_resolve_identity` single-site pin now compares `agent=`/`session=` only.
- **Amendment 1 does NOT move 64b's scope** — archive (`archived_at`, `NotArchived`, `include_archived`,
  the 5-field `Resource`) is 64d-i; the delete verb is 64d-ii. 64b builds `resource_from_row` on the
  4-field `Resource` (64d-i widens it and owns that fixture corpse). 64b's finding read seams take
  `subject=` (64d-i adds the `include_archived` keyword to the same seams). The `record<principal>`
  exact-set pin classes `finding.owner_principal` as `DISPOSED-BY-CHOICE` (am-1 §6) — the held patch's
  wording, since that pin is a shared file.
- **OF-1 (A)** touches no 64b row (findings already default to the project keep); **OF-4** is the F9 row
  as written (bound accepted, sentence + gap pin).
- **Sequence for the author:** NEW files only (kickoff §13); RED declared from `--collect-only`; the
  adversary's reference build in a `scratch_copy.sh` copy may edit the shared files there; SAT 0-failed
  before any builder.

## 8. Flags · discipline
- **FLAG (operator):** `~/.claude/CLAUDE.md`'s lore section teaches `created_by` — outside the repo; only
  the operator edits it (§5).
- **FLAG (lead):** the `project` comms brief v7 republish is a 65 cutover step — add it to 65's runbook
  beside the fleet re-brief (63-rulings §2.6 step 5).
- **Packages considered:** ONE mechanism — the refusal-teaching hook — `keep_with_trigger` pending the
  builder's read of the installed FastMCP source (I did not read it; the verdict is the builder's, cited).
- No code/tests/store touched; this doc only; no pytest; no attribution trailer on the commit.
