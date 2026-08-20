# REPORT — adversary-48b (contract-adversary, Wave 48-B: the `principal` table + PrincipalStore)

`brief-base v14 read` · `brief project v7 read`

## DELTA RE-CHECK (contract r3) — VERDICT: CONTRACT SUFFICIENT

r3 fixed all three r2 findings; I re-verified each empirically in the same scratch
(`loremaster.__file__ = /tmp/adv48b-scratch/loremaster/loremaster/__init__.py`, r3 test files
refreshed, correct reference build unchanged). Graded at working-tree r3 (untracked; HEAD still `131ba56`).

| check | result |
|---|---|
| **Satisfiability** (correct build) | **64 passed / 0 failed** — the C-DEF pin is GREEN on a correct build. (r3 report said 63; actual 64 — a trivial undercount, 0 FAILED is the point.) |
| **BLOCKER-2 CLOSED** (the security one) | widen BOTH tuples (`_PRINCIPAL_STATUSES += "archived"`, `_PRINCIPAL_ROLES += "superadmin"`) → **2 failed**: the OFFLINE `test_the_ruled_status_and_role_domains_are_EXACTLY_the_closed_set` AND the LIVE `test_a_plausible_but_unruled_status_or_role_is_rejected_by_the_store` BOTH redden. `superadmin` can no longer leak the authz domain. |
| **BLOCKER-1 not over-fixed** (positive control) | FIELD `IF NOT EXISTS` (no OVERWRITE) → `test_every_field_definition_is_OVERWRITE` + `test_no_field_definition_uses_IF_NOT_EXISTS` still RED. The `_field_statement` regex loosening (`(?:OVERWRITE\s+)?`) did NOT blind the clause pins (it tolerates OVERWRITE, still not IF-NOT-EXISTS). |
| **MINOR CLOSED** | `create` dropping `display_name`/`expires_at` → `test_create_round_trips_display_name_and_expires_at` REDs. |
| **No new gap** | WB1 subject-required (20 reds, both two-NONE pins), WB2 plain-index (5 reds incl. UPDATE theft), WB6 fill-once (idempotent-refill pin) — all still caught. |

**All three r2 blockers/minor are closed with door-build receipts; no new missing pin. VERDICT flips
INSUFFICIENT → SUFFICIENT.** Two non-blocking residuals from r2 persist and do NOT change the verdict
(the lead did not require them): (a) the routing/mutation guard's reach is "≥1 field", not "∀ fields"
(§5) — mitigated because the clause pins enforce OVERWRITE ∀ over the string; (b)
`test_create_with_explicit_non_default_role_and_status_round_trips` names `status`/`suspended` in its
docstring but only exercises `role` (create has no `status` param) — a one-line prose trim. Cleared for
the builder.

_(The r2 grade below is retained for the record — it is what r3 was built against.)_

---

## SUMMARY BLOCK (r2 — superseded by the DELTA RE-CHECK above)
- **VERDICT: CONTRACT INSUFFICIENT.** Two blocking items + one minor missing pin, all with reproductions.
- **P1 headline (satisfiability):** the reference CORRECT build scores **60 passed / 1 FAILED**. The 1 failure is a **C-DEF** (`test_status_and_role_default_to_the_least_privilege_values`) — a pin RED on a correct build, a builder trap, not a defect it caught (§0).
- **P1 headline (wrong builds):** an over-broad closed domain (`status += archived`, `role += superadmin`) **SURVIVES THE ENTIRE CONTRACT** — a surviving wrong build, i.e. a BLOCKER (MISSING-PIN-1, §3). All other wrong builds (subject-required, plain-index, every DDL-clause flip, frozen ASSERT, fill-once, no-wrap, SELECT*, silent-not-found) are CAUGHT.
- **QUANTIFIER TABLE (P1b):** §4 — one guarded row (closed-domain EXACTNESS) carries the WB5 leak receipt.
- **REACH TABLE (P1c):** §5 — the routing/mutation guard's reach is "≥1 field", not "∀ fields" (empirical leak receipt); residual, not blocking.
- **Graded:** `131ba56` · HEAD-at-report `131ba56` · SAME.
- **Scratch provenance (finding #140):** `loremaster.__file__ = /tmp/adv48b-scratch/loremaster/loremaster/__init__.py` (INSIDE scratch, via `uv run`). `scratch_copy.sh` exit 0 + `--verify-only` clean.
- **Packages considered:** none — a test contract over internal store seams (`run_query`/`execute_transaction`/`_define_*`); no package to prefer (agrees with author + design).
- **Ruling-A C-DEF-gone: CONFIRMED** — correct call-time build passes both tuple-mutation pins AND the Fork-6 docstring pin (3/3).
- **MISSING PINS:** (1) exact-closed-domain pin [BLOCKER]; (2) fix `_field_statement` so the DEFAULT pin is satisfiable [BLOCKER, C-DEF]; (3) unpinned `create` params `display_name`/`expires_at` [minor].
- **decisions-needed:** none for the operator — all three are contract-author repairs. The author's F1b/F1c/F3 conditional-pin flags remain as the author documented.

---

## 0. THE SATISFIABILITY C-DEF (BLOCKER — a pin RED on a correct build)

**C-DEF-1 — `test_status_and_role_default_to_the_least_privilege_values` is RED on a correct build.**

`test_principals_schema.py::_field_statement` (used only by this pin, L409–410) locates a field's
`DEFINE FIELD` with:

```python
re.search(rf"\bFIELD\s+{re.escape(field)}\b", statement)   # -> \bFIELD\s+status\b
```

The house emitter `surreal_schema._define_field` produces
`DEFINE FIELD OVERWRITE status ON principal TYPE string DEFAULT 'active' ASSERT …` — the
`OVERWRITE` keyword sits **between `FIELD` and the field name**, so `\bFIELD\s+status\b` matches
NOTHING and `_field_statement` fails `assert len(matches) == 1` with `got []`.

**This is a TRAP, not a caught defect.** `test_every_field_definition_is_OVERWRITE` REQUIRES `OVERWRITE`
on every field, and `test_the_slice_ROUTES_THROUGH_the_shared_ddl_emitters` requires routing through
`_define_field` (which always emits `OVERWRITE`). There is therefore **no** correct build under which
this pin is green — it is red today "for the right reason" (surface absent) and stays red on a faithful,
mutation-proof build. The builder cannot edit the contract, so they are trapped.

**Reproduction (scratch, correct reference build):**
```
FAILED …::test_status_and_role_default_to_the_least_privilege_values
  AssertionError: expected exactly one DEFINE FIELD for principal.status, got []
1 failed, 60 passed in 7.23s
```
**Proof it is SOLELY the helper:** patching only the locator to `rf"\b{re.escape(field)}\s+ON\b"` (the
field name always precedes `ON <table>`) in a scratch copy of the test → `34 passed` (all schema pins),
and the full contract goes to **0 failed**. Production code unchanged.

**Fix (author):** repair `_field_statement` to tolerate the `OVERWRITE`/`IF NOT EXISTS` token between
`FIELD` and the name — e.g. anchor `\b{field}\s+ON\s+{table}\b`, or
`FIELD\s+(?:OVERWRITE\s+|IF NOT EXISTS\s+)?{field}\b`. Then confirm the pin passes on a correct build
AND still reddens when the DEFAULT is dropped (mutation leg).

---

## 1. Satisfiability receipt (the reference CORRECT build)

I built a known-correct slice + store in the blessed scratch, per the corrected §3 (call-time ASSERT
derivation) + §5 (CRUD) + §6 (docstring naming the TUPLES):
- `surreal_schema.py`: `PRINCIPAL_TABLE`, `_PRINCIPAL_STATUSES/_PRINCIPAL_ROLES` (+ the four value
  constants), `_PRINCIPAL_FIELD_SPECS` (simple fields), `_principal_statements()` deriving the
  `status`/`role` ASSERT **at call time** from the tuples (floor idiom), `generate_principal_ddl()`,
  and `principal` **FOLDED** into `generate_ddl()`.
- `principals.py`: `Principal` (pydantic `extra="forbid", frozen=True`), `PrincipalStoreError`,
  `PrincipalNotFoundError`, `PrincipalStore` cloning the `FindingLedger` owner idiom
  (`_ensure_connection`/`_query`→`run_query`, `ensure_ready`→`execute_transaction`), an explicit-column
  `_row_to_principal` (`.get()` for `option<>` cols), CRUD that omits None columns and wraps
  `SurrealStoreError`→`PrincipalStoreError`. Module docstring names `agent`, `input_required`,
  `_PRINCIPAL_ROLES`, `_PRINCIPAL_STATUSES`, `_TRACE_DECLARED_KEYS`.

**Result:** `1 failed, 60 passed` — the single failure is C-DEF-1 (§0). With `_field_statement`
repaired, the full contract is **0-failed**, so the contract is satisfiable modulo the C-DEF.

**C-DEF-gone confirmation (ruling A):** the two tuple-mutation pins and the Fork-6 docstring pin
`3 passed` on the correct call-time build — the pre-ruling-A frozen-ASSERT C-DEF is gone (and WB4 below
re-proves the mutation pins catch a frozen build).

---

## 2. Wrong-build battery (empirical — real contract run in scratch, per wrong build)

Baseline is `1 failed [C-DEF-1] / 60 passed`. "CAUGHT" = at least one *additional* pin reddens; "LEAK"
= only C-DEF-1 reddens (the wrong build survived).

| # | Wrong build | verdict | pins that reddened (beyond C-DEF-1) |
|---|---|---|---|
| WB1 | `subject` REQUIRED (`string`, not `option<string>`) | **CAUGHT** (19) | `test_two_email_only_creates_both_none_subject_coexist` (schema, load-bearing) + `test_two_email_only_creates_coexist_via_the_store_api` (store, load-bearing) + `test_email_only_create_defaults_…` + `test_omitted_option_columns_read_back_as_none…` + 15 more (email-only is a fixture everywhere) |
| WB2 | `subject` index PLAIN (non-UNIQUE) | **CAUGHT** (5) | `test_both_unique_indexes_are_present_on_email_and_subject`, `…rejected_on_CREATE`, `…rejected_on_UPDATE_fill`, `test_duplicate_non_none_subject_on_create_raises_principal_store_error`, `test_subject_theft_raises_store_error` |
| WB3a | FIELD `IF NOT EXISTS` (not OVERWRITE) | **CAUGHT** | `test_every_field_definition_is_OVERWRITE`, `test_no_field_definition_uses_IF_NOT_EXISTS`, `test_a_principal_status_widening_lands_on_an_existing_store` (#107), `test_the_legacy_principal_row_survives_and_stays_writable` |
| WB3b | INDEX `OVERWRITE` (not IF NOT EXISTS) | **CAUGHT** | `test_both_indexes_are_IF_NOT_EXISTS_and_never_OVERWRITE` |
| WB3c | an `ALTER` statement present | **CAUGHT** | `test_the_word_ALTER_appears_in_no_statement` |
| WB3d | `principal` NOT folded into `generate_ddl` | **CAUGHT** | `test_principal_is_FOLDED_into_the_global_generate_ddl` |
| WB4 | FROZEN import-time ASSERT (pre-ruling-A idiom) | **CAUGHT** | `test_changing_the_status_tuple_changes_the_emitted_ASSERT`, `test_changing_the_role_tuple_changes_the_emitted_ASSERT` |
| **WB5a** | status domain over-broad (`+"archived"`) | **⚠ LEAK** | — none (whole contract passes) |
| **WB5b** | role domain over-broad (`+"superadmin"`) | **⚠ LEAK** | — none (whole contract passes) |
| WB5c | status domain = AGENT domain `{active,idle,input_required,retired}` | caught for WRONG reason | `test_set_status_transitions_a_known_email`, `test_set_status_on_unknown_email_raises_not_found` — only because the fixture value `"suspended"` isn't in the agent set; a plausible over-broad domain containing `suspended` would LEAK (see §3) |
| WB6 | `set_subject` fill-once (`AND subject IS NONE`) | **CAUGHT** | `test_idempotent_re_fill_of_own_current_subject_succeeds` (the F1b=A discriminator) |
| WB7a | `create` does NOT wrap engine error | **CAUGHT** | `test_duplicate_email_raises_principal_store_error`, `test_duplicate_non_none_subject_on_create_raises_principal_store_error` |
| WB7b | `get_by_*` use `SELECT *` + naive `row["subject"]` | **CAUGHT** (8) | `test_email_only_create_defaults_…`, `…coexist_via_the_store_api`, `test_list_returns_all_principals`, and 5 more (KeyError on the NONE subject) |
| WB7c | `set_status` silent no-op on unknown email | **CAUGHT** | `test_set_status_on_unknown_email_raises_not_found` |
| WB8b | `create` ignores `display_name`+`expires_at` params | **⚠ LEAK** | — none (whole contract passes); minor (§3) |
| WB8c | `create` ignores `role` param | **CAUGHT** | `test_create_with_explicit_non_default_role_and_status_round_trips` |

**WB8 migration fixture (item 8) — verified by inspection + WB3a:** `_dirty_principal_store_with_narrowed_status`
applies `generate_principal_ddl()` (NEW), then OVERWRITEs `status` to a NARROWER set, **then** inserts the
legacy row — so the legacy row is written UNDER the narrowed (OLD-world) definition, NOT after the full
DDL. This is the correct #107/§1.6 shape (a row written after the full DDL would see no hazard). WB3a
proves the leg is live: flipping FIELD to `IF NOT EXISTS` reddens `test_a_principal_status_widening_lands_on_an_existing_store`.
The `len(statuses) >= 2` assertion is a real anti-vacuity guard.

---

## 3. MISSING PINS (each with the wrong build it fails to catch)

### MISSING-PIN-1 [BLOCKER] — the exact closed domain is not pinned; an over-broad domain SURVIVES
- **Surviving wrong build:** `_PRINCIPAL_STATUSES = ("active","suspended","archived")` (WB5a) or
  `_PRINCIPAL_ROLES = ("member","admin","superadmin")` (WB5b) → **whole contract passes** (only C-DEF-1
  fails, which is unrelated).
- **Why it leaks:** the domain pins are all one-sided. `test_every_ruled_status_and_role_reaches_the_ddl`
  checks the "no-LESS" side (every *declared-tuple* value reaches the DDL); the derivation pins prove the
  ASSERT is derived FROM the tuple; the positive control iterates the *declared* tuple. Nothing pins the
  "no-MORE" side — that the tuple/ASSERT is EXACTLY the *ruled* set `{active,suspended}` / `{member,admin}`.
  The negative pins use `"not_a_status"` / `"not_a_role"` — values outside ANY plausible domain — so they
  cannot see an over-broad-but-self-consistent domain. This is THE QUANTIFIER LAW: the invariant is
  conditioned on the declared tuple instead of the ruled literal.
- **Severity:** `role ∈ {member,admin}` is the AUTHORIZATION domain (`role → AccessToken.scopes`, design R2).
  An unpinned over-broad role domain ships an un-ruled privilege value with a green contract; an over-broad
  status domain ships a state 49's suspend/admission logic never handles. This is exactly the
  security-boundary class the adversary exists to protect, and it is also the literal Fork-6 conflation
  defect (WB5c) which the docstring pin only guards in PROSE, never in the DDL.
- **The pin to add:** a pin that the emitted closed domain is EXACTLY the ruled set, discriminating on a
  PLAUSIBLE wrong value — e.g. offline `assert set(_PRINCIPAL_STATUSES) == {"active","suspended"}` and
  `assert set(_PRINCIPAL_ROLES) == {"member","admin"}`; and/or a live pin that a plausible out-of-ruled-domain
  value is REJECTED — `status="archived"` and `status="idle"` (an agent value) rejected, `role="superadmin"`
  and `role="auditor"` rejected — paired with the existing positive control. (The live form additionally
  guards a build whose client-side `set_status` validation drifts from the DDL ASSERT.)

### MISSING-PIN-2 [minor] — `create`'s `display_name` / `expires_at` params are unpinned
- **Surviving wrong build:** `create` accepts `display_name`/`expires_at` but never writes them (WB8b) →
  whole contract passes. They are always NONE, undetected.
- **Why it leaks:** no store test passes `display_name` or `expires_at` to `create` and reads them back.
  FIXTURES-MUST-DISCRIMINATE: if `create` can branch on a param, at least one pin must exercise it (as
  `test_create_with_explicit_non_default_role_and_status_round_trips` does for `role`).
- **Severity:** low — `display_name` is presentational; `expires_at` is not consumed by 48 (39/49 own it).
  But it is an unpinned parameter on the design's ruled `create` signature.
- **The pin to add:** one store pin that creates with a non-None `display_name` and a tz-aware `expires_at`
  and asserts both round-trip through `get_by_email`.

### MISSING-PIN-3 [BLOCKER, = C-DEF-1] — the DEFAULT pin is unsatisfiable
Fully covered in §0. The author must repair `_field_statement`; without it a correct build cannot pass.

---

## 4. P1b — QUANTIFIER TABLE (∀-over-inputs vs guarded)

| invariant | classification | receipt |
|---|---|---|
| TABLE = IF NOT EXISTS | ∀ over TABLE stmts (offline scans all) | safe (structural scan) |
| every FIELD = OVERWRITE | ∀ over FIELD stmts | door-build WB3a reddens it |
| no FIELD IF NOT EXISTS | ∀ over FIELD stmts | WB3a |
| INDEX = IF NOT EXISTS, never OVERWRITE | ∀ over INDEX stmts | WB3b |
| both UNIQUE indexes present (email, subject) | structural existence | WB2 |
| no ALTER | ∀ over all stmts | WB3c |
| folded into generate_ddl | structural | WB3d |
| status/role ASSERT DERIVED from tuple | mutation guard (runtime perturb) | WB4 reddens it |
| **every ruled status/role reaches DDL + reject-unknown** | **GUARDED — one-sided (no-LESS only)** | **LEAK: WB5a/WB5b survive; MISSING-PIN-1.** The bad outcome (over-broad domain) reaches through a door the pins don't watch — the negative uses an implausible value, the positive iterates the declared (possibly-wrong) tuple |
| two-NONE-subject coexist (nullable UNIQUE) | ∀-over-the-property, load-bearing | WB1 reddens; fixture discriminates (different emails — P2-confirmed §6) |
| dup non-NONE subject rejected CREATE **and** UPDATE | both doors pinned | WB2 |
| email required + unique | ∀ | WB1/WB2 |
| option<> omitted cols read None (explicit proj) + SELECT* control | behavioral | WB1/WB7b |
| empty-string subject rejected / NONE accepted | both fates forced | conditional pin (author F-#3) |
| undeclared field rejected (SCHEMAFULL) | behavioral | — (engine-enforced) |
| store defaults / role round-trip | role ∀-forced; **display_name/expires_at NOT** | WB8c catches role; WB8b LEAK → MISSING-PIN-2 |
| get_by_* → None on miss | behavioral | — |
| store wraps engine error → PrincipalStoreError | ∀ over reject paths (create/set_subject) | WB7a |
| not-found on unknown email (set_status/set_subject) | both verbs pinned | WB7c |
| NotFound ⊂ StoreError | structural (issubclass) | — |
| set_subject theft rejected (UPDATE path) | door the CREATE-only pin misses | WB2 |
| set_subject idempotent re-fill own subject | discriminator (design §5) | WB6 |
| Fork-6 docstring names both vocabularies | served-prose token set | (dropping a token reddens it) |
| migration widening lands + positive control + legacy survives+writable | behavioral #107 | WB3a |

**One guarded row leaks** (closed-domain EXACTNESS) — the MISSING-PIN-1 receipt. Every other invariant is
∀-over-inputs or its guarded door is door-build-proven closed.

---

## 5. P1c — REACH TABLE (guards the contract introduces/relies on)

Legs: WB* = empirical wrong-build in scratch against the real contract; the routing-reach probe is
empirical (below). All guards here are in-tree, so every row has an empirical leg.

| instrument | reach DERIVED vs hand-list | coverage a CHECKED variable? | effect vs proxy | one-source-by-mutation | verdict |
|---|---|---|---|---|---|
| `_require_principal_schema/_require_principals/_require_principal_ddl` (RED-now gates) | hand-list of required names | no (adding a symbol needs a manual edit) | effect (`hasattr`) | n/a | **OK** — a presence gate for RED-honesty, not a ∀-coverage guard; a missing name leaves the gate RED (loud), never a silent exemption |
| `test_the_slice_ROUTES_THROUGH_the_shared_ddl_emitters` (routing/mutation) | reach = "marker appears in `generate_principal_ddl()`" | **NO — ≥1 field, not ∀ fields** | effect (perturbs `_define_field`, checks output moved) | yes (mutates the shared emitter) | **RESIDUAL** — reach is "at least one field routes", not "every field". Empirical: hand-writing ONLY `email` (routing the rest) → the pin still **PASSES**. Mitigated: the clause pins enforce OVERWRITE ∀ over the string, so the observable #107 property holds even for a hand-written field. Note it; not blocking |
| closed-domain derivation pins (tuple-mutation) | reach = emitted DDL | proves DERIVED, not CONTENT | effect (real DDL) | yes | **derivation ✓ / content-unpinned** → the MISSING-PIN-1 gap |
| migration fixture `_dirty_principal_store_with_narrowed_status` | derives values from `_PRINCIPAL_STATUSES` | anti-vacuity `len(statuses) >= 2` present | effect (OLD→dirty→NEW, real engine) | n/a | **OK** — derived + anti-vacuity + writes legacy under OLD DDL |

Routing-reach probe receipt: with `email` hand-written as a raw `DEFINE FIELD OVERWRITE …` string and the
rest routed through `_define_field`, `test_the_slice_ROUTES_THROUGH_the_shared_ddl_emitters` → `1 passed`.

---

## 6. Fixture-discrimination (P2) + M-set spot-checks + residuals

**P2 perturbation — the load-bearing two-NONE fixture.** The pin uses two DIFFERENT emails. I perturbed a
scratch copy of the test to the SAME email and ran the PAIR:
- perturbed (same email) vs CORRECT build → **FAILS** (`principal_email` UNIQUE rejects the 2nd create
  before the subject index is reached). So the same-email fixture discriminates NOTHING — it fails even a
  correct build.
- original (different emails) vs CORRECT build → **PASSES**.
So the author's "two DIFFERENT emails" choice is load-bearing and correct (their inline comment already
names the hazard). Positive P2 result.

**M-set spot-checks (author report §3 declared-RED sets fire EXACTLY):**
- M1 (FIELD OVERWRITE→IF NOT EXISTS): declared reds `test_every_field_definition_is_OVERWRITE`,
  `test_no_field_definition_uses_IF_NOT_EXISTS`, `test_a_principal_status_widening_lands…` — **all fired**
  (WB3a). ⚠ Under-declared: WB3a also reddened `test_the_legacy_principal_row_survives…` (and, if the
  builder hand-rolls the field rather than flipping `_define_field`, the routing pin) — when
  `mutation_proof.py` runs post-GREEN with the declared set, the extra reds will show as UNDECLARED. A note
  for the builder, not a contract defect.
- M3 (drop/plainify subject UNIQUE): declared structure+CREATE+UPDATE+theft reds — **all fired** (WB2).
- M5 (freeze status ASSERT): `test_changing_the_status_tuple_changes_the_emitted_ASSERT` — **fired** (WB4).
- M7 (subject option→required): declared 4 reds — **all fired** (WB1); likewise under-declared (WB1
  reddened 19).

**Residuals (each an individual verdict):**
- `test_create_with_explicit_non_default_role_and_status_round_trips` — the NAME and docstring claim
  `status`/`suspended`, but the body only exercises `role="admin"` (design §5 `create` has NO `status`
  param — status is set only via `set_status`). Prose over-claim; `role` IS discriminated (WB8c). Trim the
  docstring's status/suspended clause. Minor served-prose accuracy.
- `pytest.raises(Exception)` (with `# noqa: B017`) on the schema Leg-2 rejection pins is broad but honest —
  the harness `run` surfaces the RAW engine error, not a typed store error, so a tight class isn't
  available there; the positive controls (e.g. the UPDATE-fill free-subject leg) prevent a
  reject-for-the-wrong-reason pass. Acceptable.
- P6 (corpse sweep) / P6b (orphaned virtues of deleted code) / P5 (test-double mutation): **N/A** —
  `principal` is a NEW table, no code is deleted or replaced, and the contract uses the live store + offline
  string checks with no fakes.
- P-PKG: no mechanism specified; "Packages considered: none" is correct (store-layer internals). Agrees
  with the author + design.

---

## 7. Verdict & what the author must do

**CONTRACT INSUFFICIENT.** Blocking:
1. **Fix C-DEF-1** (`_field_statement` regex) so `test_status_and_role_default_to_the_least_privilege_values`
   is satisfiable on a correct build (§0). Without it, no correct build passes.
2. **Add MISSING-PIN-1** — pin the EXACT ruled closed domains (`{active,suspended}` / `{member,admin}`),
   discriminating on a PLAUSIBLE over-broad value, so WB5a/WB5b/WB5c can no longer survive (§3).

Should-fix:
3. **Add MISSING-PIN-2** — one store pin exercising `create`'s `display_name` + `expires_at` params (§3).

Non-blocking notes: the routing guard's ≥1-field reach (§5), the `role_and_status` docstring over-claim,
and the under-declared M1/M7 RED sets (§6).

Everything else in this contract is strong: the load-bearing Model-B two-NONE property is pinned at BOTH
the schema and store layers with a discriminating fixture (P2-confirmed), the UPDATE-path subject theft is
pinned (the door a CREATE-only guard misses), every DDL-clause flip and the #107 dirty-store migration are
caught, the ruling-A call-time-derivation fix is mutation-proven, and error-wrapping / not-found / SELECT*
hazards are all caught.
