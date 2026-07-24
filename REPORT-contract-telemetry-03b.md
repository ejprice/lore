# REPORT-contract-telemetry-03b — the all-tools trace telemetry contract (delta row H)

brief-base v6 read

- **state: done-with-deviations.** One new file: `loremaster/tests/test_trace_telemetry.py`, **41 pins**.
- **Gates (real repo, HEAD `7d2ad32`, 2026-07-23):** `pytest -n auto` → **36 failed / 5 passed** (RED by
  design). `ruff check .` → clean tree-wide. `typecheck.sh` → **6 errors from this file**, all the
  `record_trace(caller=…)` forward ref that row F pays (§Gates).
- **The 5 greens are deliberate**, not accidental: 1 is the S7 SDK measurement (green today, RED the day
  the fact changes) + 4 are the deploy-smoke helper's own controls. **Four vacuous passes were found and
  killed** during authoring (§4).
- **SATISFIABILITY RECEIPT: 41 passed / 0 failed** against a reference build in a provenance-asserted
  scratch copy (§5). Zero pins are red on a correct build.
- **SEVEN MUTATION PROOFS, all land** (§6): no-emission → 28 RED · enumerated coverage → 25 RED ·
  module-level annotation channel → 4 RED · fresh-key-per-call → 2 RED · `total_pending`→`hit_count` →
  1 RED · error-path-only emission → 24 RED · open annotation key set → 6 RED.
- **S7's one unsettled fact is MEASURED, not delegated** (§3): `mcp` 1.27.2 mints ONE `ServerSession`
  object per MCP session → **rung 1 SELECTED, the header fallback is not needed.** The decision rule is
  encoded as a standing pin that fires if that ever changes.
- **decisions-needed (4 escalations, §2):** E1 two production symbol NAMES this contract binds ·
  E2 a two-reading spec sentence (where the unknown-annotation-key raise happens) · E3 `seq int` is
  non-`option` on a table that may already hold rows · E4 two pins depend on the sibling's `drain`.
- **flagged, not fixed (§7):** a new probed SurrealQL fact absent from the store reference; the
  design doc names `build_server` where the code says `build_mcp_server`; a scratch copy awaiting your
  disposition.
- **receipt pointers:** §1 pins · §2 escalations · §3 the S7 measurement · §4 self-caught defects ·
  §5 satisfiability · §6 mutation table · §7 residuals · §8 the deploy-smoke procedure you run.

---

## 1. What row H ships — the pins, and what wrong build each catches

All in `loremaster/tests/test_trace_telemetry.py`. Cited by class/test name, never line number.

### 1.1 Coverage as a CHECKED VARIABLE — `TestCoverageIsACheckedVariable` (7 pins)

The registered set comes from the server's OWN registration (`FastMCP.list_tools` on the product of
the production factory `build_mcp_server`); every member is driven through the REAL dispatch entry
point (`FastMCP.call_tool`); the observed set is asserted **EQUAL** — never `>=`, never a floor,
never a name list.

| pin | what wrong build it catches |
|---|---|
| `test_every_registered_tool_writes_a_trace_row` | any tool registered but not covered by the seam — set equality names both directions |
| `test_the_traced_order_is_the_dispatch_order` | a build that writes rows it never dispatched (batching, replay, one-row-per-registered-tool). Set equality alone admits it |
| `test_the_coverage_derivation_is_live_not_a_snapshot` | **the self-attack on the pin itself** — registers a tool the fixture never mentions and demands it appear on BOTH sides, proving the derivation is live rather than a stale snapshot |
| `test_a_succeeding_call_writes_its_row` | a build emitting only from the `except` arm. Most of the sweep rides error paths, so without this leg the coverage pin green-lights a seam that never traces a successful call |
| `test_a_raising_call_still_writes_its_row` | the error-path leg — "an errored pull is still a pull". A seam that traces only successes under-counts exactly the sessions where an agent is struggling |
| `test_every_row_carries_a_caller_key` | a build writing `caller` only when a session happens to resolve. `caller` is schema-`option`, so presence can only be enforced by pin (§S6v2 item 5) |
| `test_seqs_are_distinct_and_increasing_across_a_sweep` | duplicate/reused ordering keys. Asserts strict distinctness + non-decreasing, **never contiguity** — gaps are legal (store reference §5: an aborted txn burns a number) |

**The threat model is written INTO the instrument**, per CLAUDE.md's "a gate needs a threat model": this
is for the HONEST ENGINEER who adds a tool in packet 04/05/06 and never learns telemetry exists —
#147's own shape. It is NOT a boundary against an author who deliberately routes around
`FastMCP.call_tool`. So *"a tool a future packet registers goes untraced"* IS a defect; *"a hand-rolled
transport could bypass the seam"* is not, and an auditor calling the latter a defect is answered by the
docstring rather than by a fix wave.

**Why probe tools exist.** Nine synthetic tools are registered onto the built server AFTER
`build_mcp_server` returns. They are not decoration — they ARE the "tool a future packet adds" case.
A sweep over only today's built-ins cannot distinguish *coverage by seam* from *coverage by a list
somebody kept current*, which is precisely the distinction the packet turns on.

### 1.2 The seam's own fields — `TestTheSeamRecordsItsOwnFieldsHonestly` (5 pins)

`latency` is pinned with **two fixtures at different true durations** (a 60 ms sleeper with a 40 ms
floor, and an immediate tool asserted BELOW that floor) — one fixture alone is passed by any constant.
`params_hash` is pinned **stable** for identical arguments AND **discriminating** for different ones
(stability alone is satisfied by a constant). `test_argument_values_never_enter_the_trace_row` sends a
distinctive secret and asserts it appears in no field — once `lore_comms send` rides this seam the
arguments dict contains message BODIES, and a trace table is not where those belong.

### 1.3 The annotation channel — `TestTheAnnotationChannel` (6 pins)

Positive control first (`test_an_annotating_call_lands_its_domain_fields`) — *"the second row was
unannotated"* proves nothing if no row is ever annotated. Then: no leak into the next call, **no leak
after a RAISING call** (a build resetting on the success path passes the first and leaks forever after
the first error), unknown key refused **naming the key AND the legal set**, refusal is **atomic** (the
legal half of a bad payload must not land), and **seam-owned fields cannot be forged** — set equality
over `tool` is only an invariant while `tool` is seam-owned.

The annotation fixture's five values are **pairwise distinct** (`hit_count=2`, `pending=5`): a fixture
where served == pending could not tell a build writing `total_pending` into `hit_count` from a correct
one. That is the arithmetic-alignment class, and mutation **M5** confirms the fixture discriminates.

### 1.4 S7 caller identity — `TestTheS7RungSelectionFact` · `TestTheCallerKeyAtTheSeam` · `TestTheCallerKeyOverTheRealTransport` (6 pins)

Three layers, and the contract says out loud that **no single one is sufficient**:
1. **The SDK fact** (§3) — measured, pinned, carrying the decision rule in its failure message.
2. **The outcome at the seam** — same session ⇒ same key; different sessions ⇒ different keys, each
   the other's control (a constant key passes stability; a fresh-per-call key passes distinctness).
   Plus `test_the_caller_key_is_server_minted_not_caller_supplied`: opaque, safe-charset, echoing no
   caller text — catching a build keyed on client-declared `client_id`.
3. **End-to-end over the REAL streamable-http transport**, both legs, as §S7 item 3 demands.

### 1.5 Failure posture — `TestTelemetryNeverBreaksTheCall` (3 pins)

A failing store never fails the call and **never modifies the result** (v1's struck drain-render notice,
resurrected, is the wrong build); a dispatch with no request context still serves. **Every one of these
three leads with a non-vacuity guard** — see §4, they were all three vacuous when first written.

### 1.6 The `[real]` leg — `TestARealDrainWritesAnEnrichedRow` (3 pins)

A comms drain through the real `lore_comms` tool → a REAL `SurrealStore` on a virgin throwaway
database → the row read back with a real `SELECT`. Composition: trace side REAL, comms ledgers the
already-built adversarial fakes (their contract is `test_message_ledger.py`'s). Asserts
`hit_count`/`pending`/`peeked`/`agent`/`session`/`caller`/`seq` all present and correct, that `caller`
is **kept separate from** `session` (S7's no-overloading rule), and that `agent` is the **resolved
RecordID**, not the caller-supplied name. `test_a_peek_records_peeked_true` is the discrimination
control (a hardcoded `False` passes the drain pin). `test_a_generic_tool_leaves_the_comms_columns_empty`
pins the honest-unknown: a generic call records NONE, never a fabricated "content block count" proxy.

### 1.7 `seq` mint — `TestSeqIsMintedByTheStore` (4 pins)

- **Signature pin**: `record_trace` exposes **no `seq` parameter** — so no caller can mint, and a
  second writer (packet 06 tooling, a backfill) cannot start a competing series. This is #102 terrain:
  a seam-side counter would be a third mint policy beside `finding_counter`/`brief_counter`, and every
  other pin in the file would still pass.
- **Two independent store OBJECTS share one counter** — kills an in-process counter, which yields
  perfect seqs on one object and duplicate series the moment a second connection writes.
- **8-way concurrency** at the repo's mint floor (never 2-way), asserting no rows LOST and no duplicates.

### 1.8 Schema delta — `TestTheTraceSchemaDelta` (3 pins), pinned BEHAVIOURALLY

Deliberately **not** by reading `_TRACE_FIELD_SPECS` (that would be prose beside behaviour). Instead:
a generic row may omit `session`/`hit_count` and reads them back as NONE; the DDL's **guard kinds** are
asserted (fields `OVERWRITE`, table/index/sequence `IF NOT EXISTS`, and neither `BATCH` nor `START` on
the sequence per #146); and —

**`test_the_new_columns_land_on_an_ALREADY_EXISTING_trace_table` — the #107 pin, and the one I would
defend hardest.** Every other test in this file mints a VIRGIN database, and *a clean-slate fixture
structurally cannot see a migration defect* — that is why 1040 tests, a cold audit and a
contract-adversary all passed while `brief_publish` was 100% down. This pin applies the OLD trace DDL,
DIRTIES the store with a row legal only under the old world, applies the PRODUCTION emitter's DDL, and
demands both that the loosening LANDED and that the pre-existing row SURVIVED. Against the un-fixed
tree it fails with `Couldn't coerce value for field hit_count: Expected int but found NONE` — the
loosening genuinely has not landed.

### 1.9 The deploy smoke — `assert_deploy_smoke_traces` + `TestTheDeploySmokeAssertionDiscriminates`

Written as a **function with its own controls**, not as a procedure in prose: a procedure drifts and
cannot be mutation-proven. Its controls accept a good payload and reject two differently-broken ones
**for different reasons** (total vs missing-tool) — the "a probe needs a positive control" law, whose
canonical failure is a probe that rejects for a parse error and would green-light the real case.
It opens no connection, so PRODUCTION `:18500` is never touched by the suite. §8 is your procedure.

---

## 2. ESCALATIONS — four forks I did not settle silently

### E1 — two production symbol NAMES this contract binds (must go in the builder brief verbatim)

The design rulings name the *channel* ("ONE narrow helper whose key set is CLOSED") but not the symbol.
A contract cannot import a name that does not exist, so I chose — and say so rather than let the
builder discover it:

| symbol | reading A (what I pinned) | reading B |
|---|---|---|
| the enrichment helper | `loremaster.server._annotate_trace(**fields)` | any other name/shape |
| the seam class | `loremaster.server.TracingFastMCP` | — (this one IS ruled: delta row G names it verbatim) |

**Deliberate scope reduction:** `TracingFastMCP` is referenced in **exactly one class**
(`TestTheCallerKeyOverTheRealTransport`, which needs a lightweight instance to avoid lore's heavy
lifespan over the real transport). **Everything else in the file reaches the seam through
`build_mcp_server`** — so the contract pins the OUTCOME ("the server the production factory builds
traces every dispatch"), not the mechanism, and survives the builder choosing a different internal
shape. I also deliberately did **not** pin `_TRACE_ANNOTATION_KEYS` or the new `TRACE_*_FIELD`
constants: the closed key set is pinned behaviourally instead, which removes two more naming forks.

**Recommendation:** rule `_annotate_trace` and put both names in the builder brief.

### E2 — WHERE the unknown-annotation-key raise happens (a sentence with two readings)

§S6v2 item 3: *"An unknown key RAISES (deny-by-default at the merge — never a silent placeholder)."*

- **Reading A (what I pinned):** the raise happens at the `_annotate_trace` CALL, in the handler.
- **Reading B:** the raise happens in the seam when folding annotations into the row.

**I pinned A, and the reason is structural rather than aesthetic:** item 6 rules that the seam CATCHES
telemetry errors, logs, and serves unmodified. A merge-time raise would therefore be **swallowed into a
log line** — converting a deny-by-default guard into a silent no-op, which is the exact defeat class the
guard exists to prevent. A also gives atomic refusal for free (validate before store), which is a
separate pin. **Recommendation: rule A.** If you rule B, `test_an_unknown_annotation_key_is_refused_loudly`,
`test_a_refused_annotation_lands_none_of_its_keys` and `test_seam_owned_fields_cannot_be_annotated`
need re-authoring, and the swallowing problem needs its own answer.

### E3 — `seq int` is NON-`option` on a table that may already carry rows

§S6v2 item 5 rules `seq int` (not `option<int>`). Store reference §1.4 is explicit: **a NEW required
field on a POPULATED table poisons every existing row** — readable, but rejected on any future UPDATE —
and *a `DEFAULT` does not rescue it; only `option<>` does.*

**Why I judged it safe and pinned it anyway, with the bound recorded in the pin's own docstring:**
(a) trace rows are append-only by design (`record_trace`'s docstring: *"a trace is an append-only event,
never keyed/deduped"*), so poisoning-for-UPDATE has no consumer; (b) production holds **zero** trace
rows (scout-probed `:18500` read-only, 2026-07-24). **Named re-open trigger:** the day anything UPDATEs
a trace row, or any store carries pre-03b trace rows. **This is your call, not mine** — the cheap
alternative is `option<int>` plus a presence pin, which costs one nullable column and closes the class.

### E4 — two pins depend on the SIBLING author's `drain` action

`TestARealDrainWritesAnEnrichedRow` drives `lore_comms action=drain`, owned this wave by
`test_comms_tool.py`'s author. At HEAD those two pins fail with `unknown comms action 'drain'`. That is
correct and expected for a composite 03b contract, but it means **those two pins cannot go green until
both halves land** — worth knowing when you read a mid-wave builder's tail. (§5 proves they DO go green
once a minimal drain exists.)

---

## 3. THE S7 MEASUREMENT — the one fact the design could not settle, settled

§S7 designed two rungs and stated a decision rule rather than delegating a design choice. I executed
the measurement rather than passing it to a builder.

**Method** (measured 2026-07-23, host clock, `mcp` 1.27.2, this repo's locked venv): a bare `FastMCP`
with one probe tool, mounted via `streamable_http_app()`, driven **in-process over the real
streamable-http transport** by a real `mcp.client.session.ClientSession` through an
`httpx.ASGITransport` — two tool calls in one MCP session, then a second session.

```
0 {'session_obj_id': 139790940217296, 'request_id': 1, 'hdr': 'e2319c8354044090b9a3f4478a1bd694'}
1 {'session_obj_id': 139790940217296, 'request_id': 3, 'hdr': 'e2319c8354044090b9a3f4478a1bd694'}
2 {'session_obj_id': 139790940301712, 'request_id': 1, 'hdr': 'e7cf16b0fe38422da15688090c3f6081'}
SAME ServerSession object across 2 calls in ONE MCP session? -> True
DIFFERENT across two MCP sessions?                          -> True
```

**Verdict: the `ServerSession` object is PER-MCP-SESSION. Rung 1 (a server-minted uuid in a
`WeakKeyDictionary` keyed on the session object) is VALID and SELECTED. The `mcp-session-id` header
fallback is designed, available (it is present and stable, and I assert that too), and NOT NEEDED.**

**How the decision rule is ENCODED so the outcome stays visible** (not left to builder judgement):
`TestTheS7RungSelectionFact::test_the_server_session_object_is_per_mcp_session` is the standing form of
that measurement. It is **green today and goes RED** the day the SDK mints per-request, or the day
someone flips `stateless_http=True`. Its failure message carries the rule verbatim:

> *"S7 DECISION RULE FIRED: the SDK now mints a ServerSession object PER REQUEST, so rung 1 is INVALID
> — it would degenerate to a fresh key per call and every per-agent denominator would read 1. Switch to
> the designed fallback rung … Do NOT patch the object-keyed implementation."*

It carries three controls: the two same-session calls must be distinct REQUESTS (or the measurement
measures nothing); two MCP sessions must NOT share an object; and the fallback rung's own input (the
header) must be present and stable, so if rung 1 ever fails there is somewhere to fall back TO.

**Bounds I did not silently absorb:** measured on the streamable-http transport only (lore's transport);
stdio is untested by this pin, and the header rung would not exist there. §S7's self-attack table
already carries the reconnect-fragmentation and pooled-subagent cases as stated bounds, with packet 06
owing an attribution-coverage number — I have not re-derived those and do not claim to.

---

## 4. Defects I caught in my OWN contract (self-caught, before you saw them)

Reported because the interrogation is the deliverable, not just the file.

1. **FOUR VACUOUS PASSES.** `test_seqs_are_distinct_and_increasing_across_a_sweep` and all three
   `TestTelemetryNeverBreaksTheCall` pins were **green on the un-fixed tree**. `all()`, `sorted()` and
   `len(set())` are trivially true of an EMPTY list; "the call succeeded while the store was broken" is
   trivially true of a build with no telemetry at all. Each now leads with an explicit **non-vacuity
   guard** whose message says so. This is the fixtures-must-discriminate class, found in my own work by
   asking "what wrong build would this still pass?" of a GREEN test rather than a red one.
2. **`SELECT *` OMITS NONE-VALUED COLUMNS.** Two pins died with `KeyError: 'session'` on the reference
   build — the harness failing, not the finding reporting. Fixed with an EXPLICIT projection
   (`_TRACE_PROJECTION`), which reads an absent/NONE column back as `None` per store reference §2. The
   docstring records the price that section also names — *a typo'd projection degrades silently into a
   null* — and why it is affordable here: the assertions are two-sided, so a silently-nulled projection
   goes RED via the §G/§H presence pins, not green.
3. **A false red of my own making:** the first run produced 27 ERRORS, all from a `LoreConfig` slug with
   hyphens. Fixed before reporting any RED count — a collection/fixture error is not a red pin, and
   reporting one as if it were would have been exactly the noise the brief warned about.
4. **A mutation that proved nothing.** My first annotation-leak mutation (delete the ContextVar reset)
   left all 41 green — because the seam re-mints a fresh dict per dispatch, so that deletion creates no
   leak. Replaced with a module-level channel (M3b), the realistic wrong build, which lands 4 RED. A
   mutation that fails to kill is a statement about the MUTATION, not about the pin, and reporting it as
   a passing proof would have been a false all-clear.

---

## 5. SATISFIABILITY RECEIPT — 41 passed / 0 failed on a correct build

Per the C-DEF class law (20 pins RED on a correct build once shipped inside an otherwise-strong
contract), a contract goes to a builder only after it is proven satisfiable.

**Provenance first**, per #140 and the NO-WORKTREES directive: `./scripts/scratch_copy.sh` (not a
worktree, not a naive `cp -a`), which asserts every workspace member imports from INSIDE the copy:

```
loremaster  -> /home/ejprice/scratch/lore-refbuild-03b/loremaster/loremaster/__init__.py
```

**The reference build** (scratch only, never staged): `_TRACE_FIELD_SPECS` gains the five columns and
loosens `session`/`hit_count`; `_trace_statements` gains the sequence + the `(caller, seq)` index;
`record_trace` gains the new keyword-only params; `server.py` gains `_annotate_trace`, a ContextVar
channel, a `WeakKeyDictionary` caller key, `TracingFastMCP.call_tool`, the one-line instantiation swap,
and a minimal `drain` action that annotates.

**Result: `41 passed, 5 warnings` — zero pins red on a correct build**, including the harder leg (the
build satisfies ruff's and mypy's demands on the production side).

### 5.1 A load-bearing probe result the builder needs, and which the store reference does not carry

The `seq` mint must live INSIDE `record_trace`'s CREATE while the write stays `CONTENT` (because
`session` is a protected variable). I probed the four candidate shapes live on spike-surreal `:18000`
(3.2.1, throwaway namespace, removed after):

| shape | result |
|---|---|
| `CREATE t CONTENT $c SET seq = sequence::nextval("s")` | **PARSE ERROR** — `Unexpected token 'SET'` |
| `CREATE t CONTENT $c MERGE { seq: … }` | **PARSE ERROR** — `Unexpected token 'MERGE'` |
| `CREATE t CONTENT object::extend($c, { seq: sequence::nextval("s") })` | **OK** |
| `CREATE t CONTENT { tool: $c.tool, …, seq: sequence::nextval("s") }` | OK, but re-enumerates every column |

Only the third composes a bound CONTENT object with a store-side mint without hand-listing columns —
i.e. it is the one shape under which the §1.7 signature pin (`record_trace` takes no `seq` parameter)
is satisfiable. **Also measured: `sequence::nextval` starts at 0** under the default `START 0`, so `seq`
is 0-based; no pin in this file assumes otherwise. **This is a probe result, not a pattern to clone** —
the builder owns the implementation; I am reporting that a satisfying shape exists and which ones do not.

---

## 6. MUTATION PROOFS — seven wrong builds, seven kills

Method: content backup (`cp -a`, not an MD5 list — per the 2026-07-14 near-miss), one mutation at a
time against the reference build, full-file run, restore. Tree verified back to `41 passed` after the
last restore.

| # | wrong build modelled | RED |
|---|---|---|
| **M1** | the emission deleted — **#147, verbatim** | **28** incl. every coverage pin |
| **M2** | coverage by ENUMERATION (`name.startswith("lore_")`) — the six-defeats name-list, wearing a prefix | **25** incl. set equality (the probe tools vanish from the observed set) |
| **M3b** | the annotation channel is a module-level dict, never cleared | **4** — both leak pins, the atomic-refusal pin, and the generic-columns-empty pin |
| **M4** | a fresh caller key every call (≡ stateless degeneration) | **2** — the seam pin AND the real-transport pin |
| **M5** | `total_pending` written into `hit_count` | **1** — the drain enrichment pin. **This is the proof the fixture's pairwise-distinct numbers discriminate** |
| **M6** | emit only when an exception is propagating | **24** incl. `test_a_succeeding_call_writes_its_row` |
| **M7** | the annotation key set opened (deny-by-default removed) | **6** — all three refusal pins plus three coverage pins |

M2 and M6 are the two that matter most for the packet's thesis: M2 is the instrument-defeat class the
whole design is shaped against, and M6 is the build that would silently under-count exactly the
sessions packet 06 needs to see.

---

## 7. Residuals and flags — everything noticed, nothing scoped away

1. **A NEW probed SurrealQL fact that belongs in `docs/reference/surrealdb-31-capabilities.md` §2 and
   §7, which I may not edit.** Two facts, both measured 2026-07-23 on 3.2.1: (a) `CREATE … CONTENT $x`
   composes with neither `SET` nor `MERGE` (parse errors), while `object::extend($x, {…})` is the
   working shape for "bind an object AND compute a column"; (b) **`SELECT *` OMITS a NONE-valued
   column entirely** — `row["session"]` raises `KeyError`, which is *not* the same as §2's documented
   "a missing SELECT PROJECTION reads None". §2's sentence is true of projections and silent about
   `SELECT *`, and the difference cost me two pins. Both are cheap additions and would save the next
   agent the same hour.
2. **The design doc names `build_server`; the code has `build_mcp_server`.** §S6v2 item 1 says *"a
   one-line instantiation swap in `build_server`"* and §S7 says *"verified in `build_server`"*. No such
   symbol exists in `loremaster/loremaster/server.py`. Harmless for a reader, but a builder brief
   quoting it verbatim sends someone hunting. (Nothing else in the design's SDK claims was wrong — the
   `stateless_http` default, the two-line `call_tool` body, and the absent middleware API all check out.)
3. **`token_cost` / `model` remain zero-writer columns**, ruled KEPT with a re-open trigger. I pinned
   nothing about them, deliberately: a pin asserting "no writer" would go RED the day the trigger is
   legitimately pulled, which is a gate that punishes the intended future. Recorded so the absence reads
   as a decision, not an oversight.
4. **The retention decision point (design Residual 4) is untouched and unpinned by me.** All-tools
   tracing is what makes it live; my contract makes the growth real without bounding it. Nothing to do
   in 03b, but it is now a consequence of code this wave ships rather than a hypothetical.
5. **Sibling-wave observation, surfaced not acted on:** `typecheck.sh` at HEAD now reports **54** errors
   (`test_comms_tool.py` 56 lines incl. notes / `test_comms_promise_registry.py` 3 / `test_message_ledger.py` 2
   / mine 6), against the **36** the packet's entry check measured at kickoff. The growth is the sibling
   author's in-flight forward refs to `to=`/`grade=`/`peek=`/`seqs=`/`_render_comms_*`, i.e. the same
   structural class Residual 8 describes — but the packet's global-mypy-zero exit is measured against a
   number that has moved, so re-measure at the exit rather than inheriting either figure.
6. **A scratch copy awaits your disposition:** `/home/ejprice/scratch/lore-refbuild-03b` (a
   provenance-asserted `scratch_copy.sh` tree holding the reference build + its venv) and its content
   backup `/home/ejprice/scratch/refbuild-backup`. **Nothing in the repo depends on either** — every
   fact I report from them is reproduced in this file. Not a git worktree, so the worktree directive
   does not bind, but I am not deleting them unasked. Recommend: delete once you have read §5.
7. **Two `DeprecationWarning: Use streamable_http_client instead`** are emitted by the SDK's own
   `streamablehttp_client` during my transport legs — the SDK deprecating its own public entry point,
   not a defect in the contract. Noted so it is not mistaken for one, and so someone knows the newer
   name exists if the warning ever becomes an error.

---

## 8. THE DEPLOY SMOKE — the procedure you run (the deploy is yours)

After `rebuild + recreate` of BOTH containers, against the DEPLOYED artifact:

1. One live `lore_comms action=drain` and one live `lore_search` through the deployed server.
2. Read `lore_index()`.
3. Feed its `traces` block to the committed assertion:

```python
from test_trace_telemetry import assert_deploy_smoke_traces
assert_deploy_smoke_traces(index_payload["traces"])   # traces.total >= 2, BOTH tools in by_tool
```

It asserts `total >= 2` **and** that BOTH `lore_comms` and `lore_search` appear in `by_tool` — the
second half is the one that matters, because `lore_comms` alone proves only the comms leg and leaves
the all-tools seam (the entire point of the scope widening) unproven in the artifact. The assertion's
own four controls are green in the suite today, so you are running an instrument that has been shown
to fire.

**Why a helper and not three lines of prose in this report:** prose drifts, cannot be mutation-proven,
and — per #152/#153 — a citation to a repo-root `REPORT-*.md` is an address that stops resolving. The
function is committed, importable, and has its own controls. It opens no connection, so nothing in the
suite can point at PRODUCTION `:18500`.

**And why the leg is not optional at all:** pinning the source proves the RECIPE; only the running
artifact proves the CAKE. #107 (a widened ASSERT that never migrated: 1040 green, a cold audit GO, a
passing adversary, `brief_publish` 100% down) and #131 (no `git` in the image; an `OSError` swallowed
into a silent `(None, None)` for months) both lived exactly in the dev-host/container gap, and in both
the deploy smoke was the only instrument that caught it. #147 — the defect this packet fixes — is
itself that shape.

---

## 9. Tool honesty

lore-first: `lore_index` freshness was **not** checked before my lore calls, and I should say so plainly
— I resolved the tool schemas via `ToolSearch` and then answered every structure question from direct
reads of the named spec files and the source, so no graph-derived claim in this report needs the index
to have been current. **Grep/direct-read fallbacks, said out loud, all in sanctioned categories:**
(a) enumerating registration sites and the `_COMMS_ACTIONS` table (exhaustiveness — one missed site
breaks the coverage pin); (b) SDK behaviour, which is outside the project index entirely and was
settled by live introspection (`inspect.getsource` on `FastMCP.call_tool` / `get_context` /
`list_tools`) and by the §3 transport measurement; (c) test-file idioms (`_harness`, the `[real]`/`[fake]`
fixture shape, `_TRACE_PROJECTION`'s ancestor in `test_surreal_store.py`) — non-symbol textual seams.
No lore friction encountered; nothing filed.

Store law was read FIRST, as a numbered step, and is CITED throughout, never re-transcribed:
§1.1 (the DDL decision rule) · §1.4 (schema converges, DATA does not; the `option<>` requirement) ·
§1.5 (why indexes stay `IF NOT EXISTS`) · §1.6 (the virgin-DB blind spot) · §2 (protected `session`,
the silent-None projection) · §5 (native sequences, gaps are real).

Every live pin ran against the TEST store `ws://127.0.0.1:18000`. **`:18500` was never opened by
anything I ran**, and the one instrument that reads production (§8) takes a payload rather than a URL.
