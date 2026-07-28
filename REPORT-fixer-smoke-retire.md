# REPORT-fixer-smoke-retire

brief-base v7 read
brief project v7 read

## SUMMARY BLOCK

- **state:** done
- **deviations:** none to the writable set. One in-scope addition beyond the literal ask: the
  teardown's own PASS line was over-claiming (see §5) and I fixed + pinned it rather than ship a
  count defect inside the fix for a signal defect.
- **Packages considered:** `contextlib.AsyncExitStack` / `contextlib.asynccontextmanager` —
  READ: `contextlib`'s installed source for both, plus `SmokeFleet`'s existing shape. Verdict
  **bespoke (stdlib protocol, no new mechanism)**: the teardown needs the *exception in flight*
  to decide raise-vs-warn, which `__aexit__(exc_type, …)` hands over directly; `AsyncExitStack`
  adds a second object for a single resource with one exit, and `asynccontextmanager` would put
  the state (`_registered`/`_retired`) outside the object that records it. No third-party package
  is in play — this is Python's own context-manager protocol on an existing class.
- **decisions-needed:**
  1. Findings **#260** and **#261** are open and outside my writable set — both are real, both are
     yours to route (§7).
  2. The live end-to-end receipt cannot be taken from here: the full smoke writes to production
     (`:9202` / store `:18500`). Per brief I stopped and am reporting instead (§6).
- **registration sites:** ONE seam (`SmokeFleet.comms`), THREE `action="register"` call sites, all
  in `docs/eval/smoke_p8b.py` — §1 states how the set was closed, including the lore→grep fallback.
- **RED→GREEN:** 7 pins RED before the fix (the load-bearing one failing `retired_by(session) == []`
  — the leak, reproduced offline), all GREEN after. Suite **190 → 198** collected, 198 passed.
- **failure path forced:** the transcript answers gate 1's `send` with a tool-level error after two
  agents are registered; both must still be retired (§3, M2/M5 proofs).
- **gates:** `./scripts/typecheck.sh` exit 0 · `uv run ruff check .` exit 0 · `uv run pytest
  docs/eval/test_smoke_p8b.py -q -n auto` → **198 passed**, exit 0. Five mutation proofs HELD (§4).
- **comms friction filed:** **#260** (lore.yaml omits `lorerunes` — the shared-code home is invisible
  to `lore_search`, and the file is gitignored so `registration_sites.py` cannot reach it) ·
  **#261** (`docs/eval` is ungated ground: outside typecheck.sh, outside lore's index).
- **receipt pointers:** `docs/eval/smoke_p8b.py::SmokeFleet.retire_registered_agents` ·
  `SmokeFleet.__aexit__` · `run_packet_03b_gates` ·
  `docs/eval/test_smoke_p8b.py::TestTheSmokeRetiresTheAgentsItRegisters` (8 pins) ·
  §4 below for the five `scripts/mutation_proof.py` receipts.

---

## 1. The registration sites, and how I established the set was complete

**Answer: one seam, three call sites, all in `docs/eval/smoke_p8b.py`.**

| site (symbol, not line) | agents registered |
|---|---|
| `check_comms_round_trip` | `SMOKE_SENDER`, `SMOKE_ALPHA` |
| `check_broadcast_reaches_non_retired` | `SMOKE_BRAVO`, `SMOKE_CHARLIE`, `SMOKE_RETIRED` (loop) |
| — (no third registering gate; gates 4 and 6 reuse agents 1 and 3 registered) | — |

Five agents per full run. Gate 3 retires `SMOKE_RETIRED` deliberately as its fixture, so **four
per deploy leaked**, forever, which is the #258 arithmetic.

**How the set was closed, in the order I did it:**

1. **lore first, per the dogfood protocol — and it could not answer.**
   `lore_get_symbol("SmokeFleet")` → *"no Python symbol named 'SmokeFleet' is indexed"*.
   `lore_impact("smoke_p8b.SmokeFleet")` → *"never indexed"*. Root cause, read from
   `lore.yaml` `roots[tier=lore].include`: the include-list is
   `["lorescribe/**/*.py", "loresigil/**/*.py", "loremaster/**/*.py", "skills/**/*.py", "**/*.md"]`
   — `docs/eval/**/*.py` is absent. **I FELL BACK TO GREP, AND I AM SAYING SO**, which the
   project CLAUDE.md sanctions for exactly this (a non-indexed tree is not one of the three
   named grep cases, so it is a gap, not a licence — hence finding #261).
2. **A BARE, anchor-free sweep** (no `lore_` prefix, no call-paren anchor) for `register` across
   `docs/eval scripts skills scratchpad Containerfile`. Every hit adjudicated individually — the
   verdicts are in §8's residuals table, not summarised as a class.
3. **A structural argument that makes the enumeration a closed set rather than a search.** Every
   comms call in the smoke is built in ONE place: `SmokeFleet.comms` assembles the payload and is
   the only caller of `call_tool(…, COMMS_TOOL_NAME, …)`. So `action="register"` occurrences ARE
   the complete set of registrations — `grep -n 'action="register"' docs/eval/smoke_p8b.py`
   returns exactly the three sites above. This is why the fix needed no second implementation: the
   seam already existed, so the ledger and the teardown attach to it rather than to each caller.
4. **The one near-miss I checked rather than assumed.** `scripts/comms_consumer_eval.py` matches a
   `lore_comms` grep and builds rows containing `"registered_at"`. It is **not** a registration
   site: it never opens a live session (no `call_tool`, no `MCP_SERVER_URL`, no `AsyncSurreal`) —
   it *parses model-emitted tool calls* and grades them against fabricated store rows. Verified by
   reading its call surface, not by reading its name.

## 2. What changed

`docs/eval/smoke_p8b.py`:

- **`AGENT_STATUS_RETIRED = "retired"`** — a new constant beside the `SMOKE_*` block, mirroring
  `agents.py`'s terminal status the way this file already mirrors `messages.py`'s grades. It
  replaces the one hardcoded `status="retired"` in `check_broadcast_reaches_non_retired` and is
  the only spelling the teardown writes. **ONE IMPLEMENTATION**: two sites, one constant, proven
  shared by mutation (§4 M1) rather than by inspection.
- **`SmokeFleet` gains two ledgers, both fed by the single `comms` seam.** `_registered` (ordered,
  deduplicated) is appended **before** the call — a register whose response never arrived may still
  have written the row, and an unnecessary retire attempt is cheap where a missed one is permanent.
  `_retired` is added **after** `require_no_tool_error` — only a retirement the server *accepted*
  may be skipped later. Both asymmetries are commented at the site.
- **`SmokeFleet.retire_registered_agents`** — retires every registered agent not already retired,
  best-effort per agent, and **returns** the refusals rather than raising them, because whether an
  unretired agent is fatal depends on something the method cannot see.
- **`SmokeFleet.__aenter__` / `__aexit__`** — the unconditional teardown. Gates passed + a refusal
  ⇒ `SmokeCheckFailed` naming the agents and `#258`. Gate failure in flight + a refusal ⇒ a stderr
  WARNING, because the gate's diagnosis is the one worth keeping.
- **`run_packet_03b_gates` wraps its five gates in `async with SmokeFleet(...) as fleet:`** — and
  the placement is the design, not tidiness (§3).

`docs/eval/test_smoke_p8b.py`: `ToolError` + a widened `ScriptEntry` so the existing
`ScriptedSession` can answer with a tool-level error (one fake, not a second one), and
`TestTheSmokeRetiresTheAgentsItRegisters` — 8 pins.

## 3. Two design constraints that are not obvious, and would each have shipped a defect

**(a) The teardown MUST run after gate 5, and `async with` is what guarantees the order.**
`check_production_traces` asserts the production `trace` rows for the run's session are
**exactly** the `(agent, action)` multiset in `fleet.issued`. Every teardown retire is itself a
traced `lore_comms` call. Retiring anywhere earlier — the natural "clean up after gate 3" instinct
— puts rows on the store that gate 5's multiset has never heard of, turning the leak fix into a
false RED on deploy night. Pinned by `test_the_teardown_calls_are_RECORDED_in_the_issued_ledger`.

**(b) Retirement is TERMINAL, so the teardown must skip what a gate already retired.**
`AgentRegistry.touch` raises `RetiredAgentError` on a retired row *before* it reaches the
self-edge allowance, so a teardown that re-retires gate 3's deliberate corpse would end **every
otherwise-clean run** in a teardown error. Read from `loremaster/loremaster/agents.py::AgentRegistry.touch`,
not assumed. Pinned by `test_the_agent_gate_3_ALREADY_retired_is_not_retired_twice`.

**RETIRE, never delete** (sidecar S1-c): the only wire shape the teardown emits is a `heartbeat`
carrying `status="retired"`. The test helper `retired_by` asserts that shape **positively** and
spells the literal `"retired"` itself rather than reading production's constant — a helper that
reads the constant agrees with production by construction and could not see it move.

## 4. Mutation proofs — five, all HELD

Run with `scripts/mutation_proof.py` (finding #196), which diffs the observed RED set **both ways**
against a set I declared **before** any run. Every declaration was written from reasoning plus
`pytest --collect-only -q` ids, never transcribed from output; the declarations file was appended
to *before* each batch. Every proof restored the file **byte-exact** (`md5
1e9e982a08dff9b4b6c09a0081d8beb8`, equal to the working tree's md5 afterwards).

| # | mutation (the wrong build it simulates) | declared RED | exit |
|---|---|---|---|
| M1 | `AGENT_STATUS_RETIRED` → `"retyred"` — *are the two sites really sharing one constant?* | 6 (incl. `TestGateFlowDryRun::test_gate_3_flow`) | 0, HELD |
| M2 | teardown runs on the **success path only** — the natural wrong build | 2 | 0, HELD |
| M3 | roster hardcoded to `(SMOKE_SENDER, SMOKE_ALPHA)` instead of derived | 5 | 0, HELD |
| M4 | teardown refusals **swallowed silently** ("cleanup should never fail a run") | 1 | 0, HELD |
| M5 | `run_packet_03b_gates` drops the `async with` — a perfect teardown **nobody calls** | 1 | 0, HELD |

M1 is the sharing proof the ONE-IMPLEMENTATION law demands: moving the single constant reddens
gate 3's pin *and* four teardown pins together. M5 is the wiring proof — it is why the
load-bearing pin drives the real `run_packet_03b_gates` rather than the class in isolation.

**"What wrong build would still pass this?"** — the answer that produced M3: a teardown naming the
gates' agent constants as literals passes the load-bearing failure-path pin, because those *are*
the two agents that run registers. So one pin registers `"smoke-a-name-no-gate-knows"`, a name
appearing nowhere in the smoke.

## 5. The over-claim I found in my own fix

The teardown's PASS line first read *"retired N of this run's M agent(s)"*, with both numbers taken
**after** the teardown — at which point `_registered` and `_retired` are the same set. On the real
gates that renders **"5 of 5"** while the teardown performed **four** retirements; the fifth was
gate 3's fixture. A served number describing a set larger than the one it did — the count class
this repo has the most receipts against, inside the fix for a signal defect.

Fixed by computing the owed set **before** the teardown runs and pinned by
`test_the_teardown_does_not_CLAIM_the_retirement_a_gate_performed`, which reads the rendered
stdout. It is the 8th pin and the reason the count is 198 rather than 197.

## 6. What I did NOT do, and why

**I did not run the smoke against a live server.** `smoke_p8b`'s full mode targets
`http://127.0.0.1:9202/mcp` and its gate-5 reader talks to the production store `:18500`. My brief
is explicit: if the work would touch `:18500`, STOP and report. So the fix is verified **offline**
— 8 pins, 5 mutation proofs, the wiring driven through the real `run_packet_03b_gates` — and the
**live receipt is the first full smoke run after the next deploy**. Per this repo's own law that
only the running artifact proves the cake, that receipt is owed and is not mine to take.

**Concretely, what to check on deploy night:** the run should print
`PASS: teardown retired 4 agent(s) — this run registered 5 … and 1 was/were already retired by a
gate`, and a subsequent `lore_comms action=fleet` should show **no new non-retired
`smoke03b-*` rows**. Verify against `status == 'retired'` — never against the `STALE` badge, which
finding #259 measured firing on a healthy agent at 17 minutes.

**I did not verify by asserting `STALE`** anywhere, and nothing I added reads it (#259).

**I did not touch** `loremaster/loremaster/**`, the 04b-1 contract files, or `docs/plans/**`.

## 7. Gate results, including one RED that was not mine

- `uv run pytest docs/eval/test_smoke_p8b.py -q -n auto` → **`198 passed in 5.64s`**, exit 0
  (unpiped, exit captured separately). HEAD collects 190; +8 pins.
- `uv run ruff check .` → exit **0**, clean.
- `./scripts/typecheck.sh` → exit **0**; `lorerunes/lorescribe/loresigil/loremaster/skills` all OK.

⚠ **On my first gate pass, both repo-wide gates were RED** with one error each —
`loremaster/tests/test_query_tasks_bounded.py:1752: Undefined name 'SDK_CONNECTION_CLASSES'`
(mypy `name-defined` + ruff `F821`). That file is **named in my do-not-touch set** as being edited
by another agent right then, and `git diff --stat` confirmed 49 insertions there that are not
mine. I did not touch it. By my final pass the other agent had resolved it and both gates were
green. Recorded because a RED gate observed and not reported is the thing I would rather have said
twice than not at all.

Because `docs/eval` is outside `scripts/typecheck.sh`'s MEMBERS, the canonical runner does not type
my files at all. I checked them anyway under controlled resolution (both files copied to a flat
directory, strict config from the repo root): **HEAD's version and mine both `Success: no issues
found in 2 source files`** — so my change adds zero mypy errors. Run in place, mypy emits 7 errors
cascading from `Cannot find implementation or library stub for module named "smoke_p8b"`, an
artifact of `explicit_package_bases` computing the module name from the repo root. That whole
condition is finding **#261**.

## 8. RESIDUALS

Every item its own line and its own verdict.

| # | item | verdict |
|---|---|---|
| R1 | **Finding #260** — `lore.yaml`'s include-list omits `lorerunes/**/*.py`, so the workspace's designated home for SHARED CODE is invisible to `lore_search`/`lore_get_symbol`, the exact tool brief-base §6 orders agents to consult before writing a helper. Verified empirically: `lore_get_symbol("lorerunes.blankness.is_blank")` → not indexed. | **FILED, open, OUTSIDE my writable set.** Needs an operator ruling: patch the include-list, or derive it from `[tool.uv.workspace] members`. |
| R2 | **Finding #260, second half** — `lore.yaml` is gitignored (`.gitignore:36`), and `scripts/registration_sites.py` derives sites from `git grep`, which reads tracked files only. So a registration site enumerating three members is **structurally unreachable** by the instrument built to find exactly that. | **FILED.** The more serious half: re-running the mandated derivation returns a clean bill for this site forever. `lore.yaml.sample` IS tracked and should be checked for the same omission. |
| R3 | **Finding #261** — `docs/eval` (5021 lines gating production deploys) is outside `scripts/typecheck.sh` MEMBERS. Adding it is not a one-liner: 7 spurious errors, receipt and control in §7. | **FILED, open.** Needs a design choice (`mypy_path` entry / scoped override / move under a member). |
| R4 | `scripts/**/*.py` is also absent from lore's include-list — `mutation_proof.py`, `registration_sites.py`, `scratch_copy.sh`'s siblings are instruments agents are *told to use* and cannot find by search. | **RAISED here, folded into #260's suggestion (d).** Not separately filed; say the word and I will. |
| R5 | `registration_sites.py` excludes `docs/eval` via `:!docs/eval`, reasoning it is an "archived records" tree. It is live, executable, deploy-gating code. | **RAISED, noted inside #261.** Narrowing that exclusion is an operator call, not mine. |
| R6 | The live end-to-end receipt for this fix is untaken (§6) — offline verification only. | **OPEN BY CONSTRAINT, not by choice.** Owner: whoever runs the next deploy; the exact check is written in §6 so it cannot be lost. |
| R7 | `#258`'s own body proposes fix (c), `fleet` defaulting to a freshness window; sidecar S1-b **rejected** freshness exclusion in-session and S1-a ruled session-scoping instead. My work is S1-d only and changes nothing about the render. | **NO ACTION.** Recorded so a later reader does not mistake the CAUSE fix for the whole ruling. |
| R8 | Sweep hit: `docs/eval/test_smoke_p8b.py` docstring at `retired_by` mentions ``status='retired'`` in prose. | **BENIGN — prose describing the pin.** Not a wire literal. |
| R9 | Sweep hit: `TestTheSmokeRetiresTheAgentsItRegisters` class docstring mentions ``status='retired'``. | **BENIGN — prose.** Not a wire literal. |
| R10 | Sweep hit: `test_gate_3_and_the_teardown_share_ONE_retired_status_literal` contains the string `'status="retired"'`. | **DELIBERATE.** It is the scan pattern of the pin asserting that count is zero in production source. |
| R11 | Sweep hits in `scripts/search_score_survey.py` + its test (10 lines) matching bare `register`. | **UNRELATED — "pre-registered" adoption thresholds.** Not comms. |
| R12 | Sweep hits in `scripts/test_scratch_copy.py:126`, `skills/lore-deploy/scripts/test_lore_deploy.py:1873,1880`, `scratchpad/apply_edits.py` (7 lines), `scripts/test_comms_consumer_eval.py:1030`. | **UNRELATED — prose about workspace/verb/chunker registration.** No live comms agent registered. |
| R13 | `scripts/comms_consumer_eval.py` — 4 `register`-matching lines, and it names `lore_comms`. | **NOT A REGISTRATION SITE**, verified by reading its call surface (§1.4): no live session is ever opened. |
| R14 | `SmokeFleet.registered` is a new public property with no consumer outside the class today. | **DELIBERATE, low risk.** It makes the derived roster inspectable by a pin and by a future gate; it is 3 lines and is exercised indirectly by every teardown test. Delete it if you prefer a narrower surface. |
| R15 | `retire_registered_agents` catches broad `Exception` (with `noqa: BLE001`), so an `AssertionError` raised by the test fake is also collected as a "failure". | **ACCEPTED, and mitigated.** Broad catching is correct for a teardown that must never abort mid-roster; the pins therefore assert on `session.calls` (what actually went on the wire), which a swallowed error cannot fake. |
