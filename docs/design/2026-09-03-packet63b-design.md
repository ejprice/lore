# packet 63b — comms MESSAGE family + F5 runtime root-fix — design rulings

brief-base v14 read
brief project v7 read

*Author: `design-sidecar-63b` (Fable, long-running design consultant). Written 2026-09-03 against
`feat/surreal-unification` HEAD `cedb20d` (63a CLOSED, currency green). Per operator delegation
(2026-09-03) these rulings are AUTHORITATIVE for 63b — `lead-63b` implements them; the lead
escalates to the operator only after three failed contracts (the lead's call). Standing law is
CITED by address, never re-transcribed: repo `CLAUDE.md` (REACH law / INSTRUMENT 0 / TRUST two
legs / ONE IMPLEMENTATION), `docs/design/2026-08-28-packet63-retrofit-rulings.md` (= "63-rulings"
below), `docs/reference/surrealdb-31-capabilities.md` (= "store-ref").*

**Packages considered:** see §6 (filled as each mechanism is ruled).
**Reuse ledger:** see §6.
**Graded:** `cedb20d` · HEAD-at-report: `cedb20d` · SAME (this is a design doc; the code it rules
on is 63a's landed substrate at that sha).
**State:** done · **Deviations:** none · **Decisions-needed:** none (one ruled scope widening, §4.C,
carried as a named brief line) · **Filed:** the revive-on-rebuild finding (§3.1, §6).

**Reading receipts (this session, 2026-09-03):** 63-rulings §0 · §1.2 · §4.3 · §6 · §7 (SF-63-1..4)
· §10.5 · §10.6 · §10.9 (A, A-CORRECTION incl. step-2 refinement, B, C, D) — store-ref §1
(1.1–1.8) · §2 · §3 · §6 (6.1–6.6) — ledger rows: task `571ef1a…`, findings #449 #441 #436 #437
#446 — code at HEAD via `lore_get_symbol`: `governed.guarded_write` / `write_guard` /
`governed_exempt` / `active_exempt`, `_governed_contract.governed_table_raw_mutation_sites` /
`_raw_mutation_of_table` / `_mutation_verb_for_table` / `observe_governed_table_writes` /
`classify_tree_observed_write`, `store._txn.StoreHandle` / `compose`, `audit.AuditStore.append_fragment`.

---

## 0. Ruling summary (one line per item) — filled as each section lands

- **(1) F5 runtime root-fix → RULED (§1):** detection becomes an EFFECT — a before/after STATE DIFF of
  every registered governed population (rows by id + `INFO FOR TABLE`) per SDK call, observed from a
  hook in `_sdk_guard`'s class-level wrapper (the reach is the SDK class, not a module list); no verb
  list, no shape regex. `governed_exempt(name, *, statement)` is STATEMENT-scoped: classified iff
  name ∧ golden text ∧ effect predicate ∧ origin all hold. L1 is demoted to the coverage floor with a
  vendor-DERIVED keyword grammar; the governed-population set is derived from `surreal_schema`. R4-a/R4-c
  pins deleted (their own instruction). §1.7 names every clause of 10.9-A CORRECTION that changes/stands.
- **(2) #441 → RULED (§2):** `authorize_guarded` (Python leg, no effect) → ledger → ONE composed txn of
  [guarded close fragment + audit + successor UPSERT] with the conflict guard IN-STORE (`LET $hit = (UPDATE
  … RETURN AFTER); IF array::len($hit) = 0 { THROW … }` — spec-proven to abort the whole txn); on txn
  failure the ledger row is compensated. Cross-store 2PC bound named; the compensation window named + pinned.
- **(3) #436 → RULED (§3): stamp on replay FROM the ledger** — and the class is WIDER: the ledger records
  no closes, so a rebuild REVIVES every invalidated/superseded memory (filed as its own finding). Ledger
  metadata gains owner/scope/created_at/valid_until/superseded_by; `retire` verb; replay re-applies
  same-owner supersede closes. "Block member reads behind a re-migrate" REJECTED. **#437 → RULED:** ONE
  `render_subject_bound(subject)` line on every governed read render incl. the empty case; no withheld counts.
- **(4) six forks → RULED (§4):** A `send` scope by keep KEY through the lifted `governed.resolve_write_
  scope` · B drain/ack ONE txn (edge → filtered message → CAS on visible → RETURN) · C BOTH the
  `agent.owner_principal` and `message` migrate legs land in 63b (a ruled widening) · D `capability=` via
  `CommsActionSpec.requires_capability`, `register` mints, agent-name ≡ capability-name · E story/rollup
  splice the filter; the rollup message leg names its bound without identity · F message governed DDL is
  NOT at HEAD — 63b-ii adds it; `to` is a dependent (not column-governed) population.
- **(5) waves (§5):** 63b-i memory hardening + F5 instrument (memory instance; message/to cases
  RED_ADJUDICATED→ii) · 63b-ii-a message WRITE side (DDL, migrate legs, session keep, capability, send) ·
  63b-ii-b message READ side (drain/ack/story/await/rollup, bound line, F5 registries) · 63b-iii
  security-auditor over the wire. F5's message/to parametrisation RIDES ii, the instrument is its own wave.

---

## 1. THE F5 RUNTIME ROOT-FIX (task `571ef1a…` / finding #449) — RULED

### 1.1 The fork, and the two wrong builds that define it

At HEAD (`cedb20d`) F5's runtime layer (L2) is **text-keyed and frame-scoped**: `_governed_contract.
_mutation_verb_for_table` decides "this call mutated the table" by a bounded verb regex over the
resolved statement (UPSERT/UPDATE/DELETE/REMOVE), and `governed.governed_exempt(name)` blesses
*every* mutation inside its block. Two wrong builds passed every gate on the reference build (#449,
`REPORT-adversary-63a-v3.md §R4`, archived under `docs/plans/v2/receipts/2026-09-02-packet63a/`):

- **R4-a** — `UPDATE memory SET scope = $s WHERE scope IS NONE OR scope = $victim` seizes OWNED rows and
  passes a `WHERE scope IS NONE` *substring* check (22/22 green).
- **R4-c** — `INSERT … ON DUPLICATE KEY UPDATE` / `CREATE` / `RELATE` on a governed table returns
  `None` from the verb regex → **never recorded** → deny-by-default cannot fire. (SurrealDB supports
  every one of those verbs — `surrealql-tests` `statements/define/event/when_event.surql` shows UPSERT
  raising engine events; INSERT..ON DUPLICATE is spec 5776 per the task row.)

Both are ONE class: **the instrument reads the STATEMENT to infer the EFFECT**, and statements are an
open set (the reach law, CLAUDE.md "the instrument lesson" rows 1–5). The root fix is to stop reading
statements.

### 1.2 RULING — detection is an EFFECT, observed as a STATE DIFF, never a statement classification

**The property:** *"this SDK call changed the governed population's state."* It is observed, per call,
as a **before/after diff of the governed table's full state**:

- rows: `SELECT * FROM <t>` (every column; keyed by `id`) — the diff yields per-row `created` /
  `updated` (with `changed_columns`, `before`, `after`) / `deleted`;
- schema: `INFO FOR TABLE <t>` (fields / indexes / events) — a non-empty delta is a **DDL mutation**
  (`REMOVE TABLE`, `DEFINE FIELD OVERWRITE` with a change, `REMOVE INDEX`, …).

A non-empty diff on either leg IS a governed mutation by that call. **No verb list, no shape regex,
no statement text is consulted for detection.** The statement text is captured only as EVIDENCE (for
the failure message and for the exempt golden match in §1.4). This is "allowlist the safe" taken to
its end: there is nothing to classify — the world is observed. It is verb-agnostic (UPSERT / INSERT..ON
DUPLICATE / CREATE / RELATE / UPDATE / DELETE / REMOVE / `LET $x = (UPDATE …)` all move state), shape-
agnostic (a `"UP" + "DATE"` concatenation — the #444 static bound — lands at L2 exactly like a literal),
and table-generic (a relation table like `to` diffs identically to a node table).

**Why not the two engine-native alternatives (both verb-agnostic, both spec-proven on 3.2):**
`DEFINE EVENT … WHEN true THEN (CREATE witness …)` (`surrealql-tests statements/define/event/
when_event.surql` — fires per row with `$event ∈ CREATE/UPDATE/DELETE` under UPSERT) and
`ALTER TABLE <t> CHANGEFEED 1h` + `SHOW CHANGES FOR TABLE <t> SINCE …` (`tests/upgrade/define/
changefeed.surql` — one entry per create/update/delete). Each needs **test-side DDL on the REAL governed
table** whose co-residence with the shipped DDL (HNSW on `memory`, SCHEMAFULL, `TYPE RELATION … ENFORCED`
on `to`) is UNPROBED — the 63-rulings §4.4 class — and **neither sees DDL-level removal** (`REMOVE TABLE`
drops the event and the feed with the table). The state diff needs no DDL, sees DDL, and costs two
SELECTs per observed call over a test-sized table, paid only inside the F5 battery. Re-open trigger for
the alternatives: a governed table too large to snapshot in the battery (none exists; the battery's
fixtures are ≤ tens of rows).

**Self-attack — what slips the effect detector, each adjudicated (the ruling's real test):**

| shape | observed? | verdict |
|---|---|---|
| no-effect write (`SET scope = scope`) | no | not a governance event; and the COVERAGE leg (§1.5c) reds an allowlisted frame that produced no effect under the battery — the battery must exercise every frame WITH an effect |
| write-then-revert inside ONE txn (net zero diff) | no | #138 hostile-author shape (an honest developer does not write a self-cancelling transaction) — **NAMED BOUND, pinned** (a test constructs it, asserts the miss, carries the trigger "threat model → untrusted contributor") |
| two observed calls interleaved (`asyncio.gather`) | mis-attributable | **closed:** the observer holds ONE `asyncio.Lock` across before→call→after, so attribution is exact by construction; pinned (§1.6 iv) |
| mutation inside a txn that ROLLS BACK | no | correct — nothing landed; deny-by-default asks "did an unattributed write LAND". A frame whose only battery execution rolls back reds the coverage leg |
| mutation from another process (`surreal sql`, a spawned CLI) | no | #137 bound — stands, already pinned |
| the observer's own SELECT/INFO reads | excluded | they call the UNWRAPPED door (the original the guard keeps), never re-entering the guard or the observer |
| a **second governed table** mutated by the same call (e.g. `send` writes `message` AND `to`) | yes, per table | the observer diffs EVERY registered governed population per call and classifies each table's delta separately — one call, N classifications |

### 1.3 RULING — the observer's REACH is the SDK connection class, via `_sdk_guard` (EXTENDED, not cloned)

At HEAD `observe_governed_table_writes` patches the seam NAMES imported into a module set
(`local`, `governed`, + `extra_modules` derived from the allowlist's files) — a reach that is
exactly as wide as the allowlist it is meant to check (#446's own shape, one level down: a new
governed write in a module with NO allowlist entry is invisible to L2 *because* it has no entry).

**The choke point already exists and is already autouse:** `loremaster/tests/_sdk_guard.py` patches
the SDK connection CLASSES (`SDK_CONNECTION_CLASSES`, every public coroutine enumerated by
introspection — "the dangerous surface is the SDK's and grows without asking us"), walks the stack
**at CALL time** (a plain `def` wrapper — its docstring records the `async def` defeat), and attributes
each call to its immediate caller. Its door set is a PINNED PARTITION (`test_the_UNCOUNTABLE_door_set_
is_DERIVED_from_the_SDK_and_DENIES_BY_DEFAULT`): every SDK door is countable-via-`query_raw`,
uncountable-own-RPC, or in the two-method evidence-backed safe set — and `select/create/insert/upsert/
delete` are PROVEN to route through `query_raw` (read from SDK 2.0.0 source, not assumed).

**RULED:** the F5 observer is a HOOK the guard's wrapper calls — armed by the F5 battery fixture, not
autouse (§1.5c says why) — that, at call time, captures `(label=governed.active_write_guard(),
exempt=governed.active_exempt(), origin_site=<the guard's own attributed site>, statement=<the door's
args, evidence only>)` and returns the door's coroutine wrapped as `before-diff → await → after-diff →
record`. `observe_governed_table_writes(table)` keeps its NAME and its context-manager contract (63b/64
parametrise it; the meaning of `ObservedWrite` widens — `verb` becomes the effect kind per row) but
its BODY becomes "register a governed population with the guard hook". `extra_modules`,
`seam_modules_for_tree_allowlist`, and the meta-reach pin `test_the_observer_patch_set_is_derived_from_
the_allowlist` are **RETIRED** — their question ("does the observer's patch-set cover this module?")
is unaskable once the reach is the class. **Reuse ledger row:** EXTENDED `_sdk_guard` (hook), REUSED
its door partition + `require_observations` non-vacuity + `observed_call_sites` cross-check. If the
guard's wrapper has no hook seam today, adding one is a one-function change to `_sdk_guard` — the
contract names it; a second class-level patch is FORBIDDEN (two wrappers on one class is the drift
the #102 law names).

**Inherited coverage of the reach (all EXISTING instruments):** non-vacuity — `GuardReport.
require_observations` (a battery that saw zero SDK calls cannot report clean); door completeness — the
partition pin; executed-vs-static — `observed_call_sites ⊇ AST lint`. The ONE new leg: the observer
asserts it was ARMED THROUGH the guard (detach the hook → every F5 runtime pin reds with "0 observed",
never green — §1.6 v).

### 1.4 RULING — `governed_exempt` becomes STATEMENT-scoped (name + golden text + effect + origin)

**Shape:** `governed_exempt(name: str, *, statement: str)` — the exemption names ONE exact statement.
`_ACTIVE_EXEMPT` carries the `(name, statement)` pair; `active_exempt()` returns it. Production passes
its OWN module constant (e.g. `principals.MIGRATE_MEMORY_SCOPE_STATEMENT = f"UPDATE {MEMORY_TABLE} SET
scope = $scope WHERE scope IS NONE"`) both to the seam and to `governed_exempt` — ONE source in code.

**The test-side allowlist entry** (`TreeWriteAllowlistEntry`, EXTENDED) gains `statement: str` (the
GOLDEN — the adjudicated text, an oracle the adjudicator wrote down, normalised by whitespace collapse)
and `effect: Callable[[RowDelta], bool]` (the adjudicated EFFECT predicate). An observed mutation carrying
an exempt token is CLASSIFIED iff **all four legs** hold, else UNCLASSIFIED → RED:

1. `token.name == entry.exempt_name` — the channel;
2. `normalise(token.statement) == normalise(entry.statement) == normalise(observed.statement)` — the
   executed text IS the token's text IS the golden (**statement scope**: a second statement inside the
   block carries a token whose text ≠ its own → RED; R4-a's widened WHERE ≠ golden → RED);
3. `entry.effect(delta)` holds for EVERY changed row AND the schema delta is empty — for migrate:
   `before.scope is None ∧ before.owner_principal is None ∧ before.owner_agent is None ∧
   changed_columns == {"scope"}` (a golden EDITED to bless `OR scope = $victim` still reds here — the
   seized row had a scope before);
4. `observed.origin_site == entry.site` — the step-2 refinement's R1 self-containment match STANDS
   (a borrowed token from a foreign site fails).

Legs 2 and 3 are independent by construction — each has a wrong build only it catches: (2) catches a
different-shaped statement with the same effect smuggled under the token; (3) catches a golden edited
to match a seizure. The golden is NOT a second implementation (ONE IMPLEMENTATION is about policy code;
an oracle that reds when code drifts is a PIN) — and it is proven live both ways: change the production
constant → leg 2 reds; change only the golden → the coverage leg reds (no production call ever matches it).

**Label frames MAY carry an effect predicate too** (`effect` optional on non-exempt entries). It
REPLACES text-shape pins with effect pins where one exists: 10.9-C's "the bump statement touches ONLY
`importance`" becomes `changed_columns == {"importance"}` on the observed delta (strictly stronger — it
checks what happened, not what was written). REQUIRED for every 63b-new label frame (`send`: created
`message` row's `(owner_principal, owner_agent)` == the subject's pair and `scope` == the session keep;
created `to` rows have `in` == that message; `drain`: changed `to` rows have `out == subject.agent`,
`changed_columns == {"seen_at"}`, `in ∈ the served ids`; `ack`: `out == subject.agent`,
`changed_columns ⊆ {"acked_at", "ack_note"}`, `before.acked_at is None`). The R2 hand-set-label bound
(a production site setting `write_guard` without `guarded_write`) STANDS as named — an effect predicate
narrows what a hand-set label can launder but does not close the class; the docstring pin stands.

### 1.5 RULING — L1 (static) is DEMOTED to the coverage floor and its verb list is INVERTED to a derived grammar

With L2 detecting by effect at the SDK class, L1's only remaining job is **coverage**: "was every static
mutation site exercised under observation?" — a site the suite never runs is L2's blind spot (the sixth
defeat), and L1 is what names it. Its rules:

- **(a) statement-ness and target by a DERIVED grammar, not a hand verb list.** `_raw_mutation_of_table`
  keeps 63a-v's verb→operand ADJACENCY (the precision fix that rejects prose) but takes its keyword set
  from the vendor's statements index — `SURREALQL_STATEMENT_KEYWORDS` is a committed constant with a
  currency pin that DERIVES the set from the `surrealdb-docs` tier root named in `lore.yaml`
  (`…/statements/` page names) and reds on drift; a keyword the vendor lists with NO operand rule in
  the grammar reds with "classify its operand position". The grammar (operand position per keyword):
  `UPDATE|UPSERT|DELETE|CREATE <t>` · `INSERT [IGNORE|RELATION] INTO <t>` · `RELATE …->(<t>)->…` ·
  `REMOVE TABLE <t>` / `REMOVE FIELD|INDEX|EVENT … ON [TABLE] <t>` · `DEFINE TABLE <t>` /
  `DEFINE FIELD|INDEX|EVENT … ON [TABLE] <t>` · `ALTER TABLE <t>` · `REBUILD INDEX … ON [TABLE] <t>`.
  READ keywords (`SELECT`, `INFO`, `SHOW`, `LIVE`) are the safe set. A `<t>` is the literal name or the
  module constant interpolation (`{MESSAGE_TABLE}`/`{TO_RELATION}` — `table_const_hint` generalises to a
  tuple). ⚠ Where the currency pin cannot read the corpus (the in-image conformance profile, packet 01a)
  it is `RED_ADJUDICATED` in `scripts/pending_contracts.yaml` with that trigger — never skipped.
- **(b) the R4-a / R4-c bound pins are DELETED** (`TestTheAcceptedF5BoundsArePinned::test_r4a_…`,
  `::test_r4c_…`) together with the docstring clauses in `_raw_mutation_of_table` and
  `_mutation_verb_for_table` — exactly what those pins say to do "the day 63b closes it". The
  "concatenation-assembled statement" static bound (#444 class) STANDS at L1 and the instrument's
  docstring says L2 covers it by effect.
- **(c) coverage is a CHECKED VARIABLE, three legs:** (i) every L1-derived site ∈ exactly ONE allowlist
  entry (deny-by-default, stands); (ii) every allowlist entry's `frames` labels are OBSERVED mutating
  the table with a NON-EMPTY effect under the F5 battery — `runtime_observed=False` remains legal ONLY
  with a named bound + trigger (#445's shape), and 63b FLIPS `_recreate_memory_table` to observed (the
  rebuild battery runs under observation; the schema-diff leg sees `REMOVE TABLE` + re-`DEFINE`) so #445
  shrinks to nothing on the memory table; (iii) **the governed-population set is DERIVED from
  `surreal_schema`**: F5 cases = {t : t's DDL slice calls `_governed_field_specs`} ∪ {relation tables
  whose `IN` or `OUT` is in that set} — walked from the `generate_*_ddl` output (`owner_principal`
  field definitions + `TYPE RELATION IN x OUT y` clauses). At 63b that yields `memory`, `message`, `to`;
  63c adds `agent` (+ `briefed`); 64 adds `task`/`finding`. A governed population with no F5 case →
  RED. This is the growth detector ONE level up (the fifth-defeat lesson: reach as a checked variable
  over the SET of populations, not only over sites within one).
- **Why NOT autouse for the observer:** two SELECTs + one INFO per governed table per SDK call, over
  ~10k tests and 8-way contention batteries whose semantics the serialising lock would change. The
  battery arms it; leg (ii) is what makes "the battery drives every frame" a check rather than a hope.

### 1.6 Riders — and pin it like this (every one is a mutation proof; the adversary's REACH ATTACK P1c
applies to each)

| # | rider | RED when |
|---|---|---|
| i | **verb-agnostic detection** | a wrong build `INSERT … ON DUPLICATE KEY UPDATE`s / `CREATE`s / `RELATE`s into a governed table without a label → observed + UNCLASSIFIED; positive control: the same under `write_guard(<allowlisted>)` with a passing effect → classified |
| ii | **shape-agnostic detection** | a `"UP" + "DATE"` concatenated seizure → observed (the #444 static bound closed at L2, stated in the test) |
| iii | **statement scope, four legs** | (a) production constant widened `… OR scope = $victim` → leg 2 RED; (b) a second statement in the exempt block → leg 2 RED; (c) golden edited to bless the widened text → leg 3 RED; (d) a foreign site passing the real token+text → leg 4 RED; positive control: the true migrate passes all four |
| iv | **serialised attribution** | a `gather` of two labelled writes → each classified with its OWN per-call delta; remove the lock → the pin reds deterministically via a fake door that interleaves the two awaits |
| v | **reach = the guard** | detach the hook from `_sdk_guard` → every F5 runtime pin reds with `require_observations` ("0 observed"), never green; `test_the_observer_patch_set_is_derived_from_the_allowlist` is DELETED with a one-line note |
| vi | **DDL leg** | `_recreate_memory_table` under observation → schema delta observed, classified by its label; a REMOVE TABLE with no label → RED |
| vii | **population derivation** | a fixture DDL slice calling `_governed_field_specs` for a new table → the derived population set grows → RED until an F5 case exists; a relation table with a governed endpoint likewise |
| viii | **keyword currency** | delete a keyword from `SURREALQL_STATEMENT_KEYWORDS` that the corpus lists → RED; add an operand-less keyword → RED |
| ix | **no-effect / revert bounds are PINNED** (WHEN YOU CANNOT CLOSE A HOLE) | a constructed write-then-revert txn is asserted UNOBSERVED with the #138 trigger in the message; the day someone closes it the pin reds and says so |

### 1.7 What CHANGES vs 10.9-A CORRECTION + step-2 refinement, and what STANDS

| clause | disposition |
|---|---|
| CORR-1 L1 file set is an OUTPUT (whole-tree, member roots derived) | **STANDS** |
| CORR-2 "L2 matches the RESOLVED statement text at the seam" | **CHANGES** → L2 observes the EFFECT (state diff) at the SDK class; statement text is evidence only |
| CORR-2 "records originating (file, symbol) from the stack" | **STANDS** (now the guard's own attribution) |
| CORR-2 both-ways cross-check | **STANDS**, re-based: L1 sites ⊆ observed-with-effect frames (via entries); an observed mutation with no label/exempt is RED regardless of L1 |
| CORR-3 scanner discriminators (fixture-tree found / SELECT-only not flagged / concat not found and SAYS SO) | **STANDS**; the concat leg's message now says "closed at L2 by effect" |
| CORR-4 migrate is an exempt frame `governed_exempt("migrate-governed")` | **CHANGES** → `governed_exempt("migrate-governed", statement=MIGRATE_MEMORY_SCOPE_STATEMENT)`; the entry gains golden + effect |
| CORR-5 table parametrisation in `_governed_contract` | **STANDS**, widened (population set derived, §1.5c-iii) |
| step-2: classification = label present OR (exempt token ∧ site == origin) | **CHANGES** → label present OR (token ∧ golden text ∧ effect ∧ origin) |
| step-2: frames-match channel REJECTED | **STANDS** |
| step-2 R1 self-containment check on exempt entries | **STANDS** (leg 4 + the golden's single site) |
| step-2 R2 hand-set-label bound | **STANDS**, narrowed by optional effect predicates, still named |
| observer patches imported seam names + `extra_modules` (63a-v) | **RETIRED** → guard hook |
| R4-a / R4-c accepted bounds + pins | **CLOSED / DELETED** (the pins' own instruction) |
| #444 dynamic-table-name static bound | **STANDS** at L1; L2's effect leg covers a dynamically-named write to a REGISTERED population (state diff is by table, not by name-in-text) |
| #445 boot/admin frames structural-only | **SHRINKS**: `_recreate_memory_table` becomes observed via the DDL leg; `runtime_observed=False` stays legal only with a named bound |

### 1.8 Addendum — the `_sdk_guard` hook seam, concretely (read from `install()` at `cedb20d`)

`_sdk_guard.install` builds `_guarded(self, *args, **kwargs)` per SDK door: it bumps `intercepted`,
runs `_judge()` (immediate-caller attribution via `sys._getframe(2)` — depth-sensitive), records the
site, then `return original(self, *args, **kwargs)`. **There is no hook today.** The one-function
change: a module-level `_CALL_HOOKS: list[CallHook]` and, AFTER `_judge()` (so the frame depth the
walk relies on is untouched), `coro = original(self, *args, **kwargs); for hook in _CALL_HOOKS: coro =
hook(CallEvent(method=method_name, connection=self, args=args, kwargs=kwargs, site=site,
original=original), coro); return coro`. The F5 observer is one such hook: at CALL time it reads
`governed.active_write_guard()` / `active_exempt()` and returns `_observed(coro)` — an `async def`
that diffs the registered populations before/after via `event.original(event.connection, …)` (the
UNWRAPPED door — never re-entering the guard or itself), under the observer's lock. `install()` stays
autouse and hook-agnostic; the F5 battery fixture appends/removes its hook. The controls that re-arm
the guard against the test file are unaffected (`_sdk_guarded` marker semantics unchanged). Pin: a
hook that raises must not be swallowed (a broken observer is a loud test failure, never a silent
un-observation) — construct it.

---

## 2. #441 — SUPERSEDE ATOMICITY (RES-ATOM) — RULED: authorize-first, ledger, ONE composed txn with an IN-STORE conflict guard

### 2.1 The defect at HEAD, precisely

`LocalMemoryBackend.remember` (read at `cedb20d`, `memory/local.py`) runs, in order: (1) the
supersede-close through `guarded_write` — a pre-read, `pdp.authorize`, and the guarded `UPDATE …
RETURN AFTER` in ITS OWN transaction — then (2) the SQLite ledger `record`, then (3) the new-row UPSERT
in a SECOND transaction. A crash between (1) and (2) closes the predecessor (`valid_until` set,
`superseded_by` → an id that exists nowhere) and loses the successor entirely; a crash between (2) and
(3) is recoverable by replay of the successor — **but replay does NOT re-apply the close** (§3), so the
predecessor stays closed while the successor lands only at the next restore. Two windows, one root: the
close and the create are two transactions.

### 2.2 RULING — the shape (63-rulings §10.9-D realised)

1. **`governed.authorize_guarded(subject, action, *, table, row_id, audit, store) -> GuardedPlan`** —
   the PYTHON LEG split out of `guarded_write`: the pre-read through the injected `StoreHandle`, the
   `Resource` build, `pdp.authorize` (deny → `GovernedDenied`, BEFORE any durable effect), the RES-2
   refuse (`requires_audit` with no sink → `GovernedAuditUnavailable`). It MUTATES NOTHING. It returns
   a frozen plan carrying `guard_fragment`/`guard_params` (from `authorize_filter(action).to_surql()`),
   `requires_audit`, and the pre-read row (for the effect predicate + the audit `old_value`).
2. **`GuardedPlan.fragments(set_fragment) -> list[TxnFragment]`** — the guarded mutation as a FRAGMENT
   (+ the composed `audit.append_fragment` when `requires_audit`), namespaced `gw_*`/`audit_*` so
   `compose` refuses a collision. **The conflict guard moves INTO THE STORE:** the mutation fragment is
   `LET $gw_hit = (UPDATE type::record('<t>', $gw_id) SET <set> WHERE (<guard>) RETURN AFTER)` followed by
   `IF array::len($gw_hit) = 0 { THROW "governed_conflict:<t>:<id>" }` (for a DELETE the same with
   `RETURN BEFORE`). Spec-proven: `THROW` inside `BEGIN…COMMIT` aborts the WHOLE transaction — prior
   statements report *"not executed due to a failed transaction"*, `COMMIT` reports *"aborted due to a
   prior error"* (`surrealql-tests statements/transaction/throw_error_handling.surql`,
   `control_flow/transaction/throw_without_return.surql`); `IF … { THROW }` is a legal statement
   (`statements/if/control_flow.surql`). The driver's SEMANTIC root-cause selector (`_txn._domain_root_
   cause`, store-ref §3 — never position) surfaces the THROW text; `governed` maps the
   `governed_conflict:` marker → `GovernedConflict`. **Consequence:** a re-scope landing between the
   pre-read and the guarded UPDATE now rolls back EVERYTHING composed with it — the successor UPSERT
   cannot land beside an un-closed predecessor.
3. **`guarded_write` = `authorize_guarded` + `fragments` + execute** — ONE implementation; the standalone
   callers (`invalidate`, 63b's comms writes if any) are unchanged in signature. Its Python
   `row_count == 0 → GovernedConflict` branch becomes UNREACHABLE (the THROW fires first) and is
   DELETED; `row_count` is still read back from `$gw_hit`'s returned rows for `GuardedWriteResult`
   (removed-behaviour inventory: the conflict raise is PRESERVED-WITH-PIN via the THROW, the Python
   branch dropped-deliberately as dead).
4. **`remember`'s order becomes:** `plan = await authorize_guarded(…)` (deny-first, no effect) → ledger
   `record` (durable FIRST — the FP-06 law: a rebuild replays the ledger, so anything not in it is lost
   on rebuild; this order STANDS) → `write_guard("remember")` around ONE `execute_transaction` of
   `[*plan.fragments(close_set), upsert_fragment(new_row)]` → on ANY exception from that transaction
   (`GovernedConflict`, a schema ASSERT reject, transport), **compensate the ledger**: `MemoryLedger.
   delete(memory_id)` (a NEW ledger verb; SQLite, same process) and re-raise. Close + create are
   in-store atomic; deny-first is preserved; a crash after the ledger write replays the successor AND
   (per §3) its predecessor's close.

### 2.3 The bounds that STAY, named with triggers

- **Cross-store atomicity is not available** — the SQLite ledger and the SurrealDB store are two
  durability domains. The ledger is written first and is AUTHORITATIVE; the store CONVERGES to it by
  replay (§3 is what makes that convergence faithful). Trigger: never closable without a two-phase
  commit across both — not a lore goal; re-open only if the ledger moves INTO the store.
- **The compensation window** — a crash between the composed transaction's failure and the ledger
  `delete` leaves an orphan ledger row that the next restore replays. Under §3 the replay stamps the
  successor with the member's OWN pair (correct) and applies the predecessor close ONLY when the
  predecessor's owner pair equals the record's — so a conflict-because-the-row-moved orphan cannot close
  a now-foreign row by the back door. LOW: a process crash inside a ~ms window after a rare conflict.
  Pinned with the trigger.

### 2.4 Riders — pin it like this

| # | rider | RED when |
|---|---|---|
| i | in-store conflict, composed path | inject a re-scope between `authorize_guarded`'s pre-read and the txn (the §10.6-iii `acquire` wrap) → `GovernedConflict` AND the successor row does NOT exist AND the predecessor is unchanged; positive control: no re-scope → both rows in their final state in one txn |
| ii | THROW is the mechanism | delete the `IF … THROW` from the fragment → rider i's composed-path pin reds (the successor lands beside an un-closed predecessor) |
| iii | ledger compensation | force the txn to fail (a `set_fragment` violating an ASSERT) → the ledger has NO row for the successor id after the raise; positive control: success → the ledger has it |
| iv | deny-first | a member superseding a foreign row → `GovernedDenied` with ZERO ledger rows and ZERO store effect (before == after on both) |
| v | audit rides the same txn | an admin bypass supersede appends exactly +1 audit row; a rejected one appends ZERO (63-rulings §10.6-ii, extended to the composed path) |
| vi | ONE implementation | mutate `authorize_guarded`'s deny predicate → BOTH `invalidate` and the composed supersede pins red (routing proven by mutation) |
| vii | probe receipts (contract phase, :18000, `scripts/probe_*`) | (a) `LET $x = (UPDATE … RETURN AFTER); IF array::len($x) = 0 { THROW … }` inside `execute_transaction` rolls back a preceding UPSERT; (b) the fragment passes `_txn._assert_envelope_integrity` — if the engine wants a `;` inside the IF block, the fragment is TWO statements (`LET`, `IF`) in one `TxnFragment`, which `compose` already supports |

---

## 3. #436 (replay drops governance) + #437 (Subject-scope bound line) — RULED

### 3.1 #436 — the class is WIDER than the three stamps (the QUANTIFIER LAW applied before ruling)

Ground truth at `cedb20d`: `MemoryLedger` (`memory/ledger.py`) has exactly `record` / `all_records` /
`count` / `close` (`close` = the SQLite CONNECTION close, not a memory close) — no retire verb, no per-row
update; `_ledger_metadata` writes `kind / importance /
labels / source / expires_at / supersedes`; `_replay_record` → `_build_content(now=datetime.now())`
stamps NOTHING governed and sets `valid_from = created_at = now`; `restore_from_ledger` replays every
ledger id absent from the store; `rebuild_embeddings` DROPS the table and replays ALL of it, and it
AUTO-RUNS on any embedding-schema change at boot. So a rebuild loses, for every row: `owner_principal`,
`owner_agent`, `scope` (#436 as filed) — **and also** `created_at`/`valid_from` (re-stamped to the
rebuild instant) **and every close**: `invalidate` and the supersede-close are NOT recorded in the ledger
at all, so **a rebuild REVIVES every retired and superseded memory**. That is a pre-existing lifecycle
defect (old-bug per the P8d dual — adjudicated here as NOT re-pinned in its old form; FILED as its own
finding by this sidecar, see §6) and it is the same root as #436: **the ledger is the durable source
but does not carry the state the store needs to be reconstructed.**

### 3.2 RULING — stamp on replay FROM the ledger; the ledger carries governance + lifecycle; "block member reads behind a re-migrate" is REJECTED

- **Ledger metadata gains** (JSON keys — NO SQLite DDL change): `owner_principal`, `owner_agent` (bare
  ids), `scope`, `created_at` (ISO), `valid_until` (ISO | null), `superseded_by` (str | null).
  `remember` writes the first four at `record` time (the same call that exists today).
- **Closes become durable:** a NEW `MemoryLedger.retire(memory_id, *, valid_until, superseded_by)` verb (named `retire`, not `close` — `close()` is already the connection close)
  (SQLite `UPDATE … SET metadata = ? WHERE memory_id = ?` under the ledger's own connection). Called by
  `invalidate` and by the supersede path AFTER the store transaction commits (the store is the arbiter
  of a close's legality — a ledger close the store denied would replay a foreign close). Order is
  store-first for closes, ledger-first for creates; the crash window between a landed store close and
  its ledger mirror is the same LOW class as §2.3 — named, pinned. Belt for supersedes: a record whose
  metadata carries `supersedes = P` IMPLIES P's close at replay (derivable from data already in the
  ledger), so the explicit `retire` verb is load-bearing only for `invalidate`.
- **`_replay_record` reconstructs faithfully:** `_build_content` (the ONE content shape save + replay
  already share) takes the stamps as parameters — owner pair as `RecordID` links, `scope`, `created_at`
  /`valid_from` from the ledger, `valid_until`/`superseded_by` when present — and, for a record with
  `supersedes = P`, composes the predecessor close into the SAME replay transaction:
  `UPDATE type::record('memory', $p) SET valid_until = $t, superseded_by = $id WHERE superseded_by IS
  NONE OR superseded_by = $id` (idempotent), applied ONLY when P's stored owner pair equals the record's
  stamped pair. A pair mismatch (an admin's audited foreign supersede that crashed inside the §2.3
  window before its ledger mirror) is NOT re-applied — logged WARNING with both ids; the admin
  re-issues. Named bound. Legacy ledger rows (pre-63b, no governance keys) replay as NONE/NONE owner,
  NONE scope — **fail-closed** (member-invisible by the 61 predicate, admin-visible), the existing boot
  WARNING count fires, and `lore-adm migrate-governed --table memory` backfills scope as today.
- **REJECTED — "block member reads behind a re-migrate":** a global read gate keyed on a migration flag is
  a SECOND BRAIN beside the PDP (a NONE-scope row is ALREADY invisible to members by construction of the
  61 predicate — the block adds a new failure state and no isolation), and it converts a data-fidelity
  defect into a service-availability one. Stamping from the durable source removes the class instead.
- **Pin the fidelity as a PROPERTY (trust doctrine, constructed):** seed a DIRTY store — owned rows,
  legacy NONE rows, an invalidated row, a superseded pair, an admin-bypass-closed foreign row — snapshot
  `SELECT id, owner_principal, owner_agent, scope, valid_from, valid_until, superseded_by, created_at
  FROM memory`, run `rebuild_embeddings`, re-snapshot: **byte-identical**, except the named legacy
  fallbacks. Mutation proof: drop any ONE stamp from `_replay_record` → the diff reds naming the column.
  A same-dim model swap at boot (the #436 trigger) is the fixture that makes this pin the instrument
  the finding asked for.

### 3.3 #437 — RULING: ONE shared bound line, derived from the Subject, on EVERY governed read render

- **`AppContext.render_subject_bound(subject) -> Rendered`** (server.py, beside the render verbs — ONE
  function, the packet-45 derivation law: the line is DERIVED from the typed `Subject`, never restated):
  `scope: principal <principal_id> · agent <agent_id> · visible via <N> keep(s)` with
  `N = len(subject.visible_keep_ids)`. `0` renders as `visible via 0 keeps` — the 63-rulings §6
  forgery-table row (*member of no keep → names the bound, never "no memories match"*).
- **`_render_recalled_memories(recalled, *, subject)`** prepends it — INCLUDING the empty case
  (`_NO_MEMORIES_RECALLED` follows the line; the empty result is where Leg 1 matters most). Every 63b
  comms READ render (`drain`, `await`'s wake line, `story`, the rollup message leg) prepends the SAME
  line. **No withheld count anywhere** (an existence leak — 63-rulings §4.3); withheld rows stay
  server-side WARNING logs.
- **Pins:** (i) mutation — change the fixture Subject's `visible_keep_ids` → the rendered line changes;
  (ii) coverage as a checked variable — an AST/derivation pin: every render reached from a governed READ
  verb (derived from `partition_tools_by_population` × the tool's dispatch table, the #420 idiom) calls
  `render_subject_bound`; a new governed read render without it reds; (iii) hostile fixture per the
  render-safety law — a `principal_id`/`agent_id` shaped like a forged row (the ids are server-derived
  and charset-bound, but the pin constructs it anyway through `render_attributed`).

---

## 4. Comms-message-family SPEC AMBIGUITIES — both readings written, RULED (binding)

Each row: the sentence that admits two readings → reading A · reading B → the wrong build each
reading permits → RULING + rider. Ground truth cited from `messages.py` / `server.py` / `agents.py` /
`keeps.py` at `cedb20d`.

### 4.A How `send` stamps `scope` from the session keep (SF-63-1: *"`send` stamps `scope = keep:<that id>`"*)
- **A** — `send` resolves the keep by its natural key at send time: `KeepStore.get_by_key(f"session:{session}")`
  (the UNIQUE `keep.key` index — one read) and stamps `scope = keep_scope(id)`.
- **B** — `register` stores the minted keep id on the agent row (`agent.session_keep`) and `send` reads it
  from the sender's row (already read for the ghost-sender check).
- Wrong builds: under B the agent row becomes a SECOND source of truth for the session→keep mapping (a
  re-keyed keep, or a row created before 63b, silently stamps a stale/NONE scope). Under A the only
  wrong build is "keep missing at send time" → must be a DENY, never a fallback.
- **RULING: A.** `send` resolves `session:<session>` by key; the resolved scope passes through the SAME
  grant predicate `remember` uses — `pdp._grantable(subject, scope)` via `LocalMemoryBackend.
  _resolve_write_scope`'s logic, which 63b LIFTS to `governed.resolve_write_scope(subject, scope,
  *, default)` (ONE IMPLEMENTATION; `local.py` becomes a caller; reuse ledger §6). A missing session keep
  at send → `GovernedDenied` teaching *"register first (`lore_comms action=register` mints the session
  keep)"* — never the project keep, never NONE. Rider: mutation — remove the `_grantable` call in the
  lifted seam → BOTH the `remember scope=` deny pin and the `send` foreign-keep deny pin red.
- Verified, not a fork: recipients are same-session by construction — the tool resolves `to=` names *"in
  YOUR session only"* (served description) and `send` rejects unknown recipients — so a recipient outside
  the session keep's household cannot be named; SF-63-3 (DM keeps) stays DEFERRED with its trigger.

### 4.B How `drain`'s two-step §4.3 read composes with F5's runtime detection
- **A** — three seam calls: (1) edge window SELECT, (2) `message` SELECT with `read_filter`, (3) the CAS
  `UPDATE to … WHERE in IN $served` — F5 observes call (3) as a `to` mutation under label `drain`.
- **B** — ONE `execute_read_transaction`: `LET $edges = (SELECT … FROM to WHERE out = $me AND seen_at IS
  NONE ORDER BY seq LIMIT $limit); LET $visible = (SELECT id, … FROM message WHERE id IN $edges.in AND
  (<read_filter>)); UPDATE to SET seen_at = $t WHERE out = $me AND in IN $visible.id AND seen_at IS NONE
  RETURN AFTER; RETURN $visible;` — one snapshot, one round trip; F5 observes ONE call whose `to` delta
  it classifies.
- Wrong builds: under A, a message re-scoped between (2) and (3) is stamped-but-not-served (or the
  reverse) — the served set and the stamped set come from different snapshots, exactly the
  "invisible message is neither served nor stamped" guarantee §4.3 makes. Under B the risk is the
  `IN`-inside-`OR` TableScan trap — not present (plain `IN`, store-ref §2) — and `ORDER BY` on the
  projected alias (the L1 gotcha already in `drain`).
- **RULING: B** — §4.3's letter (*"two steps in ONE transaction"*) and its guarantee. `peek=True` omits
  the UPDATE statement; `since=` recovery is a read-only txn with the same filter. The served entries come
  from the txn's final `RETURN`; `stamped_seqs` from the UPDATE's `RETURN AFTER` (the DD-4 Q5 read-back
  stands). F5 label `drain`, effect predicate: every changed `to` row has `out == subject.agent`,
  `changed_columns == {"seen_at"}`, `before.seen_at is None`, and `in ∈ the returned visible ids`.
  Counts: `total_pending`/`directive_pending` stay whole-set counts over the RECIPIENT EDGES (the
  contentless-wake law, §6 accepted bound iv) — the render labels them *"pending deliveries"*, never
  *"messages you can read"* (Leg 1: the count describes the set its label claims). `ack` takes the same
  shape: resolve seqs → filter visible → CAS on visible → read back (its four-way ambiguity ruling stands).

### 4.C Is the message-row migration its own admin-verb leg of `migrate-governed`, and what about `agent`?
- **A** — 63b fills `migrate_governed(table="message")` only; it keeps REFUSING until `agent` is migrated,
  and "agent migrated" is 63c's job (SF-63-2 governs the roster there).
- **B** — 63b ships BOTH the `agent.owner_principal` backfill (a packet-62 column that already EXISTS on
  `agent`; the backfill is the §2.1 single-principal-precondition stamp) AND the `message` leg, in the §2.6
  order agent → message; 63c's SEPARATE job is agent-as-a-governed-POPULATION (scope + `fleet` filtering)
  with its own scope-backfill leg.
- Wrong builds: under A the message leg is unrunnable until 63c and the pkt-65 cutover order cannot be
  rehearsed in 63b's tests; under B the risk is 63b touching `agent` rows — but only a column 62 already
  shipped, under the existing refuse-on-multi-principal precondition.
- **RULING: B.** Two legs in 63b: `_migrate_agent_owner` (stamps `owner_principal` on every NONE-owner
  agent to THE operator principal, or REFUSES on ambiguity — the same resolution `_migrate_memory_scope`
  uses, lifted to ONE `resolve_operator_principal(principal_store)` helper) and `_migrate_message_owner`
  (`owner_agent = sender`, `owner_principal = sender.owner_principal`, `scope = keep:<project>`; REFUSES
  if any `agent.owner_principal IS NONE` remains — the §2.6 checked order). Both are exempt frames under
  §1.4 (name + golden statement + effect predicate: ∀ changed rows `before.owner_* is None ∧ before.scope
  is None`, changed columns exactly the backfilled set). ⚠ This widens 63b by one migrate leg beyond the
  brief's list; it is DERIVED from 63-rulings §0(b)/§2.1/§2.6's own text and is ruled here. The lead
  carries it as a named scope line in the wave brief.

### 4.D The `capability=` resolution seam for the comms tool (mirroring §10.5)
- **A** — `lore_comms` gains ONE optional `capability=` parameter; every message-family verb REQUIRES it
  (`send/drain/ack/await/story`), resolved through `AppContext._resolve_subject` (the ONE composition root,
  63a-ii); `register` is the exception that MINTS it (identity from the transport token via `stamp_owner`'s
  register side, as today).
- **B** — comms derives identity from `agent=` + the existing registration row, no capability.
- Wrong build under B: anyone who knows an agent's NAME acts as it — the §9 hole the capability exists to
  close. **REJECTED.**
- **RULING: A**, with the spec as the typed applicability: `CommsActionSpec.requires_capability: bool`
  (send/drain/ack/await/story = True in 63b; register = False by construction; heartbeat/brief_*/fleet =
  False in 63b, flipped by 63c — registered `RED_ADJUDICATED` rows naming 63c). `agent=` STAYS required and
  MUST equal the resolved Subject's agent name (the capability is `<name>:<secret>`); a mismatch is a
  teaching `GovernedDenied`, never a silent preference for either. The served description is the shared
  `_guarded_description` constant (#451). Rider: the routing-coverage pin derives the comms verb set from
  `_COMMS_ACTIONS` itself (the §10.5 "surfaced, not narrowed" trigger fires here) and keys the meta-pin on
  each verb's EFFECT — a verb with `requires_capability=True` and no `_resolve_subject` call in its handler
  reds.

### 4.E Which reads carry the `read_filter`, and the rollup's message leg
- `story` (`messages_for_task`: `SELECT … FROM message WHERE task_id = $t`) and the rollup's message leg
  (`message_activity_since`) read `message` DIRECTLY — they splice `AND (<read_filter>)` (63-rulings §1.2
  item 2's splice contract), no two-step needed. `await` peeks the recipient edges — its WAKE count stays
  the edge count (accepted bound iv); it serves no content.
- **The rollup lives on `lore_tasks`**, whose task/finding legs are ungoverned until 64. **RULING:**
  `lore_tasks rollup` gains the optional `capability=` in 63b; WITHOUT it the message leg is not served
  and the render names the bound (*"messages: identity required — pass capability="*) — a named bound,
  never an unfiltered leg and never a withheld COUNT; WITH it the leg is filtered and carries
  `render_subject_bound`. 64 makes the whole verb capability-required.

### 4.F Where the message governed-column DDL lands
- 63-rulings §1.2 item 4 says `_message_statements` calls the ONE emitter; **at `cedb20d` it does NOT**
  (`surreal_schema._message_statements` emits `_MESSAGE_FIELD_SPECS` + the `to` edge only). Not a fork —
  a fact the lead's brief must carry: 63b-ii adds `_governed_field_specs()` + `_governed_index_statements
  (MESSAGE_TABLE)` to `_message_statements` (the §4.1 DDL, `option<>` columns, plain `IF NOT EXISTS`
  indexes on `scope` and `owner_principal`). The `to` edge gets NO governed columns (§4.3: policy lives on
  `message`); it is an F5 DEPENDENT population (§1.5c-iii derivation), which is exactly why the population
  derivation includes relation tables with a governed endpoint.

---

## 5. WAVE STRUCTURE — recommendation (the lead sets orchestration; this is the dependency-honest cut)

**Answer to the lead's direct question first:** the F5 INSTRUMENT (§1 — effect detection, guard hook,
statement-scoped exempt, derived grammar, population derivation) lands as its OWN wave on the MEMORY
instance where every existing pin lives; its `message`/`to` PARAMETRISATION rides the message-family
wave, because the registries classify writes that do not exist until that wave. Build the net before the
fish — the R4 lesson was writes landing under an instrument that could not see them.

| wave | contents | why together | writable set (disjoint by design) |
|---|---|---|---|
| **63b-i — memory hardening + F5 root-fix** | §1 (all), §2 (#441), §3.1–3.2 (#436 widened), §3.3 `render_subject_bound` on recall | one domain (`governed.py`, `memory/local.py`, `memory/ledger.py`, `principals.py::_migrate_memory_scope`, `_governed_contract.py`, `_sdk_guard.py`); every pin family already exists here; the `message`/`to` F5 cases are created `RED_ADJUDICATED(owner=63b-ii)` | `loremaster/governed.py`, `memory/*`, `principals.py` (memory leg only), `tests/_governed_contract.py`, `tests/_sdk_guard.py`, `tests/test_memory_*`, `server.py` (recall render only) |
| **63b-ii-a — message family, write side** | §4.F DDL · §4.C two migrate legs · SF-63-1 session keep at `register` (`get_or_create_keyed("session:<s>", type="session", keeper=first registrant)`; foreign-principal register → teaching deny) · §4.D `capability=` + `requires_capability` · §4.A `send` scope stamp via the lifted `governed.resolve_write_scope` · F5 `message`/`to` registries GREEN for `send` | the writes and the identity that stamps them; the migrate legs need the DDL; `send` needs the keep | `surreal_schema.py`, `messages.py` (send), `agents.py`/`keeps.py` (register keep), `server.py` (comms tool + spec), `principals.py` (agent/message legs), `tests/test_comms_*`, F5 registries |
| **63b-ii-b — message family, read side** | §4.B `drain`/`ack` one-txn shapes · §4.E `story`/rollup filter + `await` · `render_subject_bound` on every comms read · F5 registries GREEN for `drain`/`ack` · §6 forgery-table rows for the comms surfaces | reads depend on the stamped rows and the keep; the F5 effect predicates for drain/ack need the txn shapes | `messages.py` (reads), `server.py` (comms renders + rollup), tests |
| **63b-iii — security-auditor** | 63-rulings §6 target over the WIRE on the REAL tables: F3 fixture (≥2 principals × ≥2 agents, disjoint households, one shared session string) × every read verb of both tools; the Leg-2 forgery table; SF-63-1 as the headline | after ii-b is GREEN; a NO-GO opens a fix wave, not a re-design | report-only |

- **Each wave is a full pipeline** (contract → adversary → build → cold audit), per 63-rulings §1.1; no
  wave skips the adversary because it "implements what the last adversary asked for" (CLAUDE.md
  "A CONTRACT NEEDS AN ADVERSARY BEFORE A BUILDER").
- **Split triggers** (63-rulings §1.4's sizing law, cited not re-transcribed): if 63b-i's contract exceeds
  the adversary's second round without converging, split §2/§3 (memory fidelity) from §1 (F5) — F5 first.
  ii-a/ii-b are pre-split above because 63a's history (five contract rounds on ONE wave) is the receipt
  that a comms wave carrying writes AND reads AND identity AND DDL AND migration will not converge in
  three; the lead may merge them back if ii-a's contract lands in one round.
- **Adversary pointers per wave:** i → REACH ATTACK (P1c) on §1.5c's three coverage legs and the
  population derivation; the QUANTIFIER attack on §3.2's fidelity pin (∀ lifecycle states, not the three
  stamps). ii-a → F4 anti-injection ∀ write verbs (no argument moves the stamp; a foreign `scope=` denies).
  ii-b → the served-COUNT-is-over-the-served-SET (§6 item 2) and the two-step snapshot guarantee.
- **Currency at every close-out:** `uv run python scripts/pending_contract_gate.py --currency` solo, no
  masking pipe (the 63a close-out lesson, finding #452) — the `RED_ADJUDICATED(owner=63b-ii…)` rows are
  the instrument working; a `RED_ORPHANED` is the disease.

---

## 6. Packages considered · Reuse ledger (brief-base §1 / §6)

**Packages considered** (each: mechanism · library · what was READ · verdict):
- **Effect-based mutation detection** · `surrealdb` SDK 2.0.0 · READ: `_sdk_guard.py`'s derivation over
  the SDK classes (every data door builds SurrealQL and posts it via `query_raw`; the SDK exposes NO
  statement parser or classifier) · **bespoke** — a test-substrate state-diff observer. ⚠ No PyPI
  SurrealQL parser was surveyed: the ruling REMOVES the need for statement classification rather than
  hand-rolling a parser; if a later ruling wants text classification, run `package-scout` first.
- **Engine-native change capture** · SurrealDB `DEFINE EVENT` / `CHANGEFEED` · READ: `surrealql-tests`
  `statements/define/event/when_event.surql`, `tests/upgrade/define/changefeed.surql`,
  `bench/util/changefeed-populated.surql` · **keep_with_trigger** — trigger: a governed table too large
  to snapshot in the battery (none today).
- **In-store conflict guard** · SurrealQL `THROW` inside `BEGIN…COMMIT` + `IF … { THROW }` · READ:
  `statements/transaction/throw_error_handling.surql`, `control_flow/transaction/throw_without_return.
  surql`, `statements/if/control_flow.surql` · **replace** (the Python `row_count == 0` conflict branch).
- **Ledger lifecycle fields** · stdlib `json` + `sqlite3` · READ: `memory/ledger.py` (metadata already
  round-trips `json.dumps`/`json.loads`; `record` is `INSERT … ON CONFLICT DO UPDATE`) · **bespoke**
  (two small verbs on the existing table; SQLite's `json_set` considered and rejected to keep ONE
  serialisation path).
- **Row diff for the observer** · stdlib dict equality keyed by `id` · **bespoke** (flat rows; a deep-diff
  package was not read because none is needed — say so if a nested column ever joins the diff).

**Reuse ledger** (new symbols — `| new symbol | lore query run | returned | disposition |`):
| `governed.authorize_guarded` / `GuardedPlan` | `lore_get_symbol loremaster.governed.guarded_write` | one monolithic authorize+compose+execute | **EXTENDED** `guarded_write` (split; it becomes the composition of the two) |
| `governed.resolve_write_scope` | `lore_get_symbol LocalMemoryBackend._resolve_write_scope` | exists on the memory backend only | **EXTENDED** (lifted to `governed`; `local.py` and `send` both call it) |
| `principals.resolve_operator_principal` | `lore_get_symbol loremaster.principals._migrate_memory_scope` | inline block in one function | **EXTENDED** (lifted; all three migrate legs call it) |
| `MemoryLedger.retire` / `MemoryLedger.delete` | ledger API map (`record`/`all_records`/`count`/`close`) | no per-row update or delete exists | **HAND-ROLLED** (nothing to reuse; two SQL statements) |
| `AppContext.render_subject_bound` | `lore_search "render recalled memories Subject scope bound"` | `_render_recalled_memories(recalled)` takes no subject; no bound line anywhere | **HAND-ROLLED** (one derived-from-Subject line; every governed read render calls it) |
| `_sdk_guard.CallEvent` / `_CALL_HOOKS` | read `_sdk_guard.install` | no hook seam in `_guarded` | **EXTENDED** `_sdk_guard` |
| `SURREALQL_STATEMENT_KEYWORDS` + operand grammar | `lore_get_symbol _raw_mutation_of_table` | bounded verb regex | **EXTENDED** (same function; derived set) |
| `governed_populations()` (test substrate) | `lore_get_symbol _message_statements` / `_governed_field_specs` | the emitter exists; no consumer-set derivation | **HAND-ROLLED** (a walk over `generate_*_ddl` output) |
| `TreeWriteAllowlistEntry.statement` / `.effect` | `_governed_contract` dataclasses | fields absent | **EXTENDED** |

**Deviations:** none from the brief. **Decisions-needed (operator):** none — one scope WIDENING is ruled
within delegated authority and must be a named line in the lead's wave brief: §4.C (the `agent.
owner_principal` backfill leg lands in 63b). **Filed by this sidecar:** the revive-on-rebuild lifecycle
finding (§3.1) — number in the `lore_findings` ledger, `area=memory-backend`, sibling of #436.

## 7. Riders roll-up — the "and pin it like this" index (contract author / adversary / auditor)

- §1.6 i–ix (F5: verb/shape-agnostic detection, four-leg exempt scope, serialised attribution, reach =
  the guard, DDL leg, population derivation, keyword currency, pinned no-effect/revert bounds) ·
  §1.8 (a raising hook is loud, never a silent un-observation).
- §2.4 i–vii (#441: composed-path conflict, THROW is the mechanism, ledger compensation, deny-first,
  audit rides the txn, ONE implementation by mutation, two probe receipts).
- §3.2 fidelity property (dirty-store byte-diff across `rebuild_embeddings`; drop-one-stamp mutation) ·
  §3.3 i–iii (bound line: mutation, coverage-derived, hostile fixture).
- §4.A (lifted grant predicate proven by mutation across `remember` and `send`) · §4.B (drain/ack effect
  predicates; count labels name their set) · §4.C (both migrate legs as four-leg exempt entries; order
  precondition refuses) · §4.D (`requires_capability` typed on the spec; verb set derived from
  `_COMMS_ACTIONS`; agent-name ≡ capability-name) · §4.E (rollup message-leg bound, never a count).
- §5: currency gate solo at every close-out; `RED_ADJUDICATED` rows carry an owner and a trigger.
- Every wave's cold audit re-runs the F5 battery and ONE randomly chosen mutation proof from §1.6/§2.4
  (the lead's one-receipt-per-batch law).

*Every ruling above is within the authority delegated for 63b (operator, 2026-09-03). The lead
implements; a contract that fails three times is the lead's escalation, not mine. Standing by for
follow-ups — this doc grows by dated addenda, never by silent rewrites of a ruled section.*

---

## 5.1 ADDENDUM (2026-09-03, `lore_comms` q:63b-i-split #9001) — 63b-i SPLIT into i-a (F5 instrument) → i-b (memory fidelity): RULED, with the one coupling that matters

**The split is APPROVED and F5-first is the right order** — i-b's new mutation shapes must land under a
net that can already see them (the R4 lesson stated as an ordering). Two questions, ruled:

### Q1 — the `_recreate_memory_table` observed-flip (§1.5c-ii / §1.6-vi): **i-a owns the flip AND its pin — and the flip drags in a work item §1 did not spell out.**

Ground truth at `cedb20d` (`memory/local.py`): `_recreate_memory_table` wraps ONLY the `REMOVE TABLE IF
EXISTS memory` in `write_guard("_recreate_memory_table")`, then calls `await self.ensure_ready()` —
which re-applies `generate_memory_ddl()` through `execute_transaction` **outside any guard**. Under §1's
DDL leg (`INFO FOR TABLE` diff), that re-DEFINE is a schema mutation of a governed population with NO
label → UNCLASSIFIED → RED. And it is not only the rebuild path: **every backend fixture calls
`ensure_ready()` at construction**, so on a virgin test DB the FIRST DDL apply is a schema delta
(no table → table) on every F5 battery run. Therefore the DDL leg is NON-SATISFIABLE on ANY fixture
until the boot DDL is classified — that is F5 instrument completeness, not #436, and it is i-a's:

- **`ensure_ready` becomes an allowlisted DDL frame** in i-a: `write_guard("ensure_ready")` around its
  `execute_transaction` (a label, not an exempt token — it is not member-reachable but it is the same
  frame every boot; the honest-developer threat model is satisfied by the label + the effect predicate).
  **Effect predicate:** the schema delta equals the diff produced by applying `generate_memory_ddl()`
  itself (DERIVED — the golden is the emitter's own output, never hand-written), and the ROW set is
  unchanged (a DDL frame that moves rows is RED). This generalises: in ii-a the same entry covers
  `_message_statements`' first apply (`DEFINE TABLE OVERWRITE to …` re-applied unchanged is a no-delta,
  store-ref §1.5's probed "does not rebuild").
- **The flip itself:** `_RECREATE_ENTRY.runtime_observed=False` → removed; the i-a battery drives
  `rebuild_embeddings` under observation with the CURRENT replay and asserts the arc
  `REMOVE TABLE` (label `_recreate_memory_table`, schema delta: table gone, rows gone) →
  `ensure_ready` (schema delta: table back, per the derived golden) → `_replay_record` UPSERTs
  (row deltas, label present). #445's bound shrinks to nothing on `memory`; its clause in
  `observe_governed_table_writes`'s docstring is deleted in i-a.
- **i-b's relationship to this entry:** #436 changes `_replay_record`'s EFFECT (more columns stamped;
  a predecessor-close UPDATE inside the replay txn) — it WIDENS `_UPSERT_ENTRY`'s effect predicate for
  the `_replay_record` frame (a per-entry DATA change in the test substrate), never the instrument.
  `_recreate_memory_table` and `ensure_ready` are UNTOUCHED by #436.

### Q2 — other §1 ↔ §2/§3 couplings that would make a §1 coverage leg non-satisfiable without #441/#436's sites: **NONE.** i-a goes 0-failed against the CURRENT memory sites. Enumerated, leg by leg (§1.5c):

| §1 leg | against the current tree | i-b's later touch |
|---|---|---|
| (i) every L1-derived site ∈ one entry — with the WIDENED keyword grammar | the widened grammar derives the SAME four sites (`_upsert_fragment` UPSERT · `_reinforce` UPDATE · `_recreate_memory_table` REMOVE · `_migrate_memory_scope` UPDATE): the schema emitter's `DEFINE …` literals interpolate `{name}`/`{table}`, not `{MEMORY_TABLE}` → the #444 dynamic-name static bound (covered at L2 by the DDL leg); SF-63-5's prose fails the verb→target adjacency. The contract asserts the derived set as an OUTPUT — a surprise site is classified in i-a | #441 adds NO new literal site in `local.py` (the close fragment is BUILT by `governed.GuardedPlan.fragments`, whose `UPDATE type::record('{table}', …)` is a dynamic-name literal → not derived; L2 sees its effect under `remember`'s label); #436's predecessor-close `UPDATE type::record('{MEMORY_TABLE}', $p) …` in `_replay_record` IS a new derived site → i-b registers it on `_UPSERT_ENTRY`'s sibling (frame `_replay_record`) |
| (ii) every entry's frames observed with a NON-EMPTY effect | `remember` (create) · `_replay_record` (restore battery) · `_reinforce` (⚠ fixture alignment: the bump must change the value — seed a row BELOW the importance ceiling) · `_recreate_memory_table` + `ensure_ready` (Q1) · `_migrate_memory_scope` (NONE→keep) · `guarded_write` via `invalidate` and the CURRENT two-txn supersede — all present today | #441 collapses the supersede to ONE call under `remember`'s label producing TWO row deltas; i-b WIDENS `remember`'s effect predicate to `{created row owned by subject} ∪ {updated predecessor: changed ⊆ {valid_until, superseded_by}}`. `guarded_write`'s own entry stays "exactly one governed row changed or deleted" (its standalone callers) |
| (iii) population derivation | yields `{memory}` at `cedb20d` — no relation table has `memory` as an endpoint; `_message_statements` does not yet call `_governed_field_specs` (§4.F). One case → satisfiable. ii-a's DDL grows the set → the `message`/`to` cases are the `RED_ADJUDICATED(owner=63b-ii)` rows | none |
| four-leg exempt for migrate (§1.4) | i-a introduces `principals.MIGRATE_MEMORY_SCOPE_STATEMENT` + `governed_exempt(name, *, statement)` (production edits in i-a's writable set); golden + effect satisfiable against the current statement | none (§4.C's two NEW legs are ii-a's entries) |
| reach = the guard hook (§1.3/§1.8) | `_sdk_guard` hook + `require_observations` — independent of every memory change | none |
| §1.6-ix no-effect / revert bound pins | constructed in i-a | none |

**So the dependency runs ONE way, i-a → i-b:** i-b's contract is written AGAINST i-a's LANDED instrument
and its satisfiability receipt is run with the F5 battery as the regression floor — an i-b mutation that
lands unlabelled or off-predicate reds i-a's pins, which is the net working. i-b's writable set therefore
INCLUDES the F5 allowlist DATA (`test_memory_enforcement_*` entries / effect predicates) and EXCLUDES the
instrument (`_governed_contract.py`'s detector, `_sdk_guard.py`'s hook) — a change i-b needs in the
instrument itself is a STOP-and-flag back to this doc, never a quiet edit.

**Writable-set cut, for the briefs:** i-a — `loremaster/governed.py` (exempt API only), `principals.py`
(`_migrate_memory_scope`: the statement constant + kwarg), `memory/local.py` (`ensure_ready` label,
`_recreate_memory_table` flip only), `tests/_governed_contract.py`, `tests/_sdk_guard.py`,
`tests/test_memory_enforcement_*` (+ deletion of the R4-a/R4-c pins). i-b — `governed.py`
(`authorize_guarded`/`GuardedPlan` split), `memory/local.py` (`remember`/`invalidate`/`_replay_record`/
`_build_content`), `memory/ledger.py` (`retire`/`delete`), `server.py` (recall render + `render_subject_
bound`), the F5 allowlist DATA, `tests/test_memory_*` for #441/#436/#437.

---

## 1.9 ADDENDUM (2026-09-03, `lore_comms` q:63b-i-a-adversary #9007 — adversary-63b-i-a INSUFFICIENT, 1st contract) — five design-adjacent items RULED; two of my own examples CORRECTED

Graded against `REPORT-adversary-63b-i-a.md` (measured in a provenance-asserted scratch at `519c0bb`) +
finding #454. The two class-(A) missing pins (the classifier must RUN a label entry's effect predicate ∀
label frame; `governed_populations()`'s reach must be a checked variable, not `frozenset({memory})`) are
CONFIRMED as exactly §1.4 / §1.5c-iii's intent — the contract adds them; in i-a EVERY memory label entry
carries an effect predicate (`remember`: created rows only, owner pair non-NONE — owner ≡ subject stays
F4's pin; `_reinforce`: `{importance}`; `_replay_record`: created rows only at i-a, widened by i-b;
`_recreate_memory_table`: schema-only delta, rows gone; `ensure_ready`: item 4 below; `guarded_write`:
exactly one row changed or deleted).

### Item 1 — §1.4's module-level constant was WRONG; the exempt statement is FUNCTION-LOCAL. CONFIRMED.
L1 attributes a literal to its DEFINING scope (`_enclosing_functions` → `<module>`), and R1
self-containment (10.9-A step-2, standing) already demands literal + seam call + exempt entry in ONE
symbol — my `principals.MIGRATE_MEMORY_SCOPE_STATEMENT` example violated my own retained rule. **RULED:**
the adjudicated statement is a FUNCTION-LOCAL variable inside `_migrate_memory_scope`, passed to BOTH
`governed_exempt(…, statement=stmt)` and `run_query(statement=stmt)` — still ONE source, now derived at
the entry's own site. §1.4's example text is superseded by this paragraph; the contract's
`_MIGRATE_GOLDEN` docstring must stop teaching the module-constant trap (F-TRAP-2). The general rule,
stated once: **an exempt-adjudicated statement lives in the function that executes it — never a module
constant** (the L1 scan is the enforcer: a module-scope orphan is RED by construction, which is correct).
"Make L1 attribute a module constant to its using function" is REJECTED — a name-flow analysis is a new
reach surface for no gain.

### Item 2 — populations derive from `_governed_field_specs` CALLERS, not from `owner_principal` presence. CONFIRMED; §1.5c-iii's wording corrected.
`agent.owner_principal` is a packet-62 DIRECT field, so "walk the `owner_principal` field definitions"
wrongly yields `{memory, agent, briefed, to}` (F-TRAP-1). **RULED:** `governed_populations()` = {t :
`_<t>_statements` (or any `surreal_schema` emitter for t) CALLS `_governed_field_specs`} — an AST walk
over `surreal_schema.py` — ∪ {relation tables whose `_define_relation_table(name, IN, OUT)` call has IN
or OUT in that set} — also AST. At `cedb20d`: `{memory}`; ii-a's DDL grows it to `{memory, message, to}`.
Missing-pin #2's synthetic-schema mutation proof is the instrument (a fixture source with a new
`_governed_field_specs` caller MUST grow the output).

### Item 3 — the observer mechanism: GOTCHA-A/B/C are RULED as the mechanism; §1.8's `event.original` wording is superseded.
- **(a) Observe at `query_raw` ONLY.** Measured (#454): `.query` delegates to `.query_raw` internally and
  the guard patches both, so a hook firing on `.query` re-enters through the patched `query_raw` and
  deadlocks on the observer's held non-reentrant lock. `query_raw` is the narrow waist every SurrealQL
  statement passes through — the harness's own door partition proves it (`COUNTABLE_DOORS` routes
  select/create/insert/upsert/update/delete through `query_raw`; the UNCOUNTABLE own-RPC doors
  `begin/commit/cancel/live/kill/use` carry no statement). **Reach statement, so this is not a hidden
  constant:** observer reach ≡ the `query_raw` door ≡ the set the partition pin derives; the pin
  `test_the_UNCOUNTABLE_door_set_is_DERIVED…` is cited BY NAME in the observer's docstring as the
  reach's evidence, and a door the SDK adds that bypasses `query_raw` lands in UNCOUNTABLE and reds
  that pin — the seventh defeat is thereby caught one instrument over. The before/after reads use the
  UNWRAPPED `query_raw` — `_sdk_guard` sets `_guarded.__wrapped__ = original` (one line, inside the
  `_sdk_guard` EXTENSION already ruled), and the observer reads `type(conn).query_raw.__wrapped__`.
- **(b) ONE persistent dispatcher + a registry.** The dispatcher hook is appended to `_CALL_HOOKS` once
  (at `_governed_contract` import); `observe_governed_table_writes(table)` only REGISTERS `(table,
  sink)` in a registry the dispatcher consults and un-registers on exit. The detach pin (§1.6-v) then
  clears `_CALL_HOOKS` and proves zero observations — a per-observe append would re-arm behind the
  clear and red the pin on a correct build (measured, GOTCHA-B). §1.3's sentence "the F5 battery fixture
  appends/removes its hook" is superseded: the fixture registers populations; the hook is persistent.
- **(c) Origin is captured at exempt CONTEXT ENTRY — and WITHOUT a filename skip-list.** At SDK-call
  time the immediate production caller is always `_txn.py`'s driver, so leg-4's origin cannot come from
  the call-time walk. **RULED:** `governed_exempt` becomes a small CLASS context manager (`__enter__` /
  `__exit__` doing the contextvar set/reset) instead of a `@contextlib.contextmanager` generator, and
  `__enter__` captures `sys._getframe(1)` — the frame executing the `with` statement, exactly one up,
  with NO `contextlib.py` frame in between — as `(repo-relative file, co_name)`. This removes the
  `contextlib.py`-by-filename skip GOTCHA-C had to discover (a skip-list is the relocated-constant
  antipattern, even a two-entry one). The token in `_ACTIVE_EXEMPT` is a frozen `ExemptToken(name,
  statement, origin)`; `active_exempt()` returns it or `None`. `write_guard` is unchanged (the label leg
  never consults origin). Pin: a helper that calls `governed_exempt` on the migrate frame's behalf
  yields an origin ≠ `_migrate_memory_scope` → leg 4 RED (the borrowed-token construction, retained).
- **(d) The serialising lock stays** (§1.6-iv); the adversary's measurement confirms the 8-way concern
  never arises because the observer is armed only inside F5 battery blocks.

### Item 4 — F-TRAP-3: the `ensure_ready` oracle is ENGINE-RENDERED; the DDL-text regex is RETIRED. RULED (d), superseding (a)/(b)/(c).
The oracle was written against the DDL STRING and the engine reports array-element definitions as
`embedding.*` / `labels.*` — precisely the #107/#131 class the adversary names ("the test environment is
a fiction"), and any of (a)/(b)/(c) keeps a hand-model of the engine's implicit expansions alive (the
next one — an `object` field, an `array<object>` path — reds again). **RULED:** the expected schema is
obtained by CONSTRUCTION: apply `generate_memory_ddl()` (the SAME emitter, same dim) to a virgin
harness database (`_surreal_harness.unique_database()` — one more mint, a session-scoped fixture keyed
by dim) and read `INFO FOR TABLE memory` there; `_effect_ensure_ready` is then `after.schema ==
oracle.schema` as MAPS (`fields` / `indexes` / `events` keys + their rendered definition strings — dict
equality, no regex anywhere) AND `rows_before == rows_after`. `_memory_ddl_object_names()` is deleted.
Trust-doctrine construction, not reasoning: the oracle is the engine's own rendering of the same
recipe, so it is correct for every implicit expansion the engine has or will have. Pin the oracle's
non-vacuity: a synthetic DDL with one extra field applied to the oracle DB must make the comparison red.

### Item 5 — writable-set fork: origin capture is WITHIN "exempt API only". RULED, not a widening.
"Exempt API" = `governed_exempt` (now the class form) + `active_exempt` + the `_ACTIVE_EXEMPT`
contextvar + the `ExemptToken` value type — leg-4 origin capture is a field of that token, produced by
that function. Nothing else in `governed.py` moves in i-a; the `authorize_guarded`/`GuardedPlan` split
remains i-b's. `_sdk_guard.py` gains exactly two lines beyond the hook (`__wrapped__` on `_guarded`;
nothing else) — inside the extension already in i-a's writable set.

**Superseded text in this doc (a reader must not follow the older wording):** §1.4's
`principals.MIGRATE_MEMORY_SCOPE_STATEMENT` example (→ item 1) · §1.5c-iii "owner_principal field
definitions" (→ item 2) · §1.3 "the F5 battery fixture appends/removes its hook" and §1.8's
`event.original` read guidance (→ item 3) · §5.1's ensure_ready golden phrasing "the schema delta
equals applying generate_memory_ddl()" is kept in intent and made CONCRETE by item 4.

---

## 2.5 ADDENDUM (2026-09-04, `lore_comms` q:63b-i-b-2.2gap #10002 / finding #456) — the `governed_conflict:` marker → `GovernedConflict` mapping: RULED as a TYPED classification in `_txn.py`; `_txn.py` joins i-b's writable set, SCOPED

### The gap, as measured (contract-63b-i-b, `scripts/probe_supersede_throw_rollback.py`, :18000, exit 0)
The rollback CORE of §2.2 holds: the in-store `LET … RETURN AFTER; IF array::len(…) = 0 { THROW
"governed_conflict:<t>:<id>" }` aborts the whole composed `BEGIN…COMMIT`, the preceding UPSERT is rolled
back, `_assert_envelope_integrity` accepts the fragment, and the engine surfaces the marker in the raw
`query_raw` result (`kind='Thrown'`, `"An error occurred: governed_conflict:probe_t:target"`). What §2.2
left UNSPECIFIED is the last hop: `_run_verified_transaction` raises a plain `SurrealStoreError` whose
message is a CLASSIFIED generic label + the server-log hint — by design (the `_classify_engine_error`
hygiene boundary: *"never a slice of `raw_result` itself"*) — so the marker never reaches `governed`. My
§2.2 sentence *"the driver's semantic root-cause selector surfaces the THROW text; `governed` maps the
marker"* conflated SELECTING the entry (which `_domain_root_cause` does, as measured) with SURFACING its
text (which the boundary forbids). Superseded by this section.

### RULING — Reading A, sharpened to the seam's own shape (Reading B REJECTED: it clones the verification and re-exposes raw text — ROUTING-IS-NOT-SHARING and the hygiene boundary in one move)
1. **ONE marker, ONE label, ONE typed error, in `_txn.py`, beside their precedents:**
   `_GOVERNED_CONFLICT_MARKER = "governed_conflict:"` (a FIXED prefix OUR code authors into the THROW — the
   classification key; the `<t>:<id>` suffix is free-form forensics), `_ERROR_CLASS_GOVERNED_CONFLICT`
   (a fixed teaching label: *"governed conflict — the guarded row moved between authorization and the
   write; re-authorize and re-issue"*), and `class TxnGovernedConflictError(SurrealStoreError)` — the
   exact shape of `TxnContentionExhaustedError`: a SUBCLASS so every existing `except SurrealStoreError`
   keeps catching it, a generic message + `_SERVER_LOG_HINT`, and **NO attributes parsed from the text**
   (the caller already holds table and row).
2. **Where it slots — the classifier, not the witness.** `_classify_engine_error` gains the marker branch
   (membership check → the fixed label, like `_ASSERT_VIOLATION_MARKER`). `_rollback_verdict` is
   UNCHANGED: a governed conflict is a DOMAIN rejection (`is_conflict=False`) — retrying it re-runs the
   same stale guard and THROWs again, so it is never retried; `_domain_root_cause` already selects the
   Thrown entry (first non-cascade — measured).
3. **BOTH raise sites map label → type through ONE helper.** `_run_verified_transaction` (behind
   `execute_transaction` AND `execute_read_transaction` — the composed `remember` path and the standalone
   `guarded_write` path) and `run_query` (the single-statement seam, which also consumes
   `_classify_engine_error`) build their domain rejection via a new shared
   `_domain_rejection_error(error_class, message) -> SurrealStoreError` that returns
   `TxnGovernedConflictError` iff the label is the governed one, else the plain type. Two raise sites,
   one mapping — never a cloned `if label == …` at each.
4. **`governed` catches the TYPE, never text:** `except TxnGovernedConflictError as error: raise
   GovernedConflict(f"… {table}:{row_id} …") from error` — in `guarded_write` (standalone) and in the
   composed path (`remember`, which also runs its ledger compensation on this path per §2.2 step 4).
   The contract's rider-i/ii pins keep `pytest.raises(governed.GovernedConflict)` — the intended type stands.

### Why this is hygiene-compliant BY THE BOUNDARY'S OWN TERMS (not by the "it's our string" argument)
The classifier still returns a FIXED label, never a slice; the typed error still carries no raw text;
the `<t>:<id>` suffix rides only into `_log_rollback` (server-side, structured), exactly as an ASSERT's
echoed value does today. That the THROW text is authored by `governed` rather than echoed by the engine's
validation is true, but the ruling does NOT lean on it — a future THROW that interpolated a bound value
would be equally safe, because the exception never carries the text.

### Writable-set grant — `_txn.py` JOINS i-b, SCOPED to exactly:
the marker constant · the label constant · `TxnGovernedConflictError` · the `_classify_engine_error`
branch · `_domain_rejection_error` and its two call sites (`_run_verified_transaction`, `run_query`) ·
the module docstring line that lists the error classes · the classification tests that EXTEND the
existing families (`test_surreal_store.py::TestDomainRejectionErrorType` and the `test_retry_seam.py`
marker/label enumerations — extended, never cloned). Everything else in `_txn.py` — the retry driver,
`_rollback_verdict`, the cascade markers, the envelope checks — is DO-NOT-TOUCH for i-b. Production-
touching (the shipped driver) → pre-authorized under CLAUDE.md's pre-production status; no operator
gate; the cold audit re-runs the R4/#120 seam pins.

### Riders — and pin it like this
| # | rider | RED when |
|---|---|---|
| i | typed on BOTH raise sites | a `governed_conflict:` THROW rejection via `run_query` AND via `execute_transaction`/`execute_read_transaction` each raise `TxnGovernedConflictError` (construct both, on the test store); positive control: an ASSERT rejection on each still raises the plain `SurrealStoreError` |
| ii | hygiene, both directions | the raised message contains NEITHER the row id NOR the table name from the THROW suffix (byte check) AND `_log_rollback`'s structured record DOES carry the raw text (the forensics survive — positive control) |
| iii | never retried | a governed-conflict rollback makes EXACTLY one attempt (count via the `acquire` wrap / the guard's intercept count), never a retry; positive control: a `can be retried` rollback retries |
| iv | one source | mutate `_GOVERNED_CONFLICT_MARKER` (or the THROW prefix in `GuardedPlan.fragments`) → the standalone `invalidate` conflict pin AND the composed supersede conflict pin BOTH red — proving the two paths share the marker and the mapping |
| v | the label-set enumerations gain the member | whatever pin enumerates `_ERROR_CLASS_*` / the marker constants reds until the new member is registered — that is the instrument, not noise |
| vi | `GovernedConflict` end-to-end | rider i/ii of §2.4 unchanged — a re-scope injected between `authorize_guarded`'s pre-read and the composed txn raises `governed.GovernedConflict`, successor absent, predecessor untouched, ledger compensated |

**Superseded text in this doc:** §2.2 step 2's last two sentences (*"the driver's SEMANTIC root-cause
selector … surfaces the THROW text; `governed` maps the `governed_conflict:` marker → `GovernedConflict`"*)
→ read: the selector picks the Thrown entry; the CLASSIFIER maps it to `TxnGovernedConflictError`;
`governed` catches the TYPE. §5.1's i-b writable set gains the scoped `_txn.py` grant above.
