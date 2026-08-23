# REPORT — adversary-61a-w4 (contract-adversary on the append-only `audit` store substrate)

brief-base v14 read
brief project v7 read

---

## ⭐⭐ ROUND 3 RE-GRADE (2026-08-23 — identity-at-write / §9 forensics delta; CURRENT verdict)

**VERDICT: CONTRACT SUFFICIENT.** The identity-at-write delta (71→76 pins, operator-ratified §9 forensics) is correctly and discriminatingly pinned. Graded at `e92bd0f` (wave uncommitted; revised contract re-synced into the provenance-asserted scratch, `loremaster.__file__` = `/tmp/lore-adv-61a-w4/loremaster/loremaster/__init__.py`). Every row below is a wrong-build run against the revised contract on the live store `ws://127.0.0.1:18000`. (The 3 Round-1/2 blockers stay closed — re-confirmed by the lead; not re-run here.)

| Delta asked | Result | Receipt |
|---|---|---|
| **(1) actor_email + actor_agent_name are DENORMALIZED string VALUE cols (not links); a write stores the exact provided value** | ✅ | Schema pin `test_actor_email_and_actor_agent_name_are_required_non_empty_string_VALUES` asserts `TYPE STRING` + no `RECORD<` + `ASSERT STRING::LEN` + no `OPTION`. Behaviour: `test_append_captures_the_EXACT_identity_provided` stores the caller's DISTINCT email/name. Correct build 76/76. Emitted DDL: `DEFINE FIELD OVERWRITE actor_email ON audit TYPE string ASSERT string::len(string::trim($value)) > 0`. |
| **(2a) LINK-ONLY build (no denormalized value) → survives-delete pin REDS** | ✅ | Built it (dropped the value cols + writes). `test_actor_identity_survives_a_hard_principal_delete` → **RED** (`assert None == 'alice@example.com'`), + the capture pin + round-trip pin. |
| **(2b) LAZY-DERIVED (read-time deref) → MUST red; does the contract discriminate write-captured from lazy-derived?** | ✅ **YES — discriminated by the BEHAVIOURAL pins** | The two behavioural pins read the identity when the source principal is UNAVAILABLE: the capture pin uses an UNSEEDED `actor_principal` (`admin_alice`) + a distinct caller email; the survives-delete pin DELETES the principal first. Any read-time/derive-from-link value → NONE → RED. ⚠ The SCHEMA field pin alone does NOT discriminate (a computed field passes its text checks) — but the behavioural pins cover it, so the contract AS A WHOLE discriminates. **Engine bound (measured, `ws://127.0.0.1:18000`):** on 3.2.4 a true read-time-lazy field `<future> { actor_principal.email }` is a **PARSE ERROR** ("expected a kind name") — NOT constructible; the only store-side computed option, `VALUE actor_principal.email`, WRITE-captures (`pre=['x@e.com'] post-delete=['x@e.com']` — survives) yet still reds the capture pin. So no lazy build that passes the whole contract exists on this engine. |
| **(3) append/append_fragment take identity as CALLER INPUT (no store-side fetch/coupling/race) — store-side fetch is caught** | ✅ | Built a store-side-derive (`VALUE actor_principal.email`, ignores caller) → capture pin **RED** (`AuditStoreError`: the unseeded principal derefs to NONE → non-empty ASSERT rejects → rolls back). `append`/`append_fragment` signatures REQUIRE `actor_email`/`actor_agent_name` (no default — `_append_call_kwargs` supplies them; identity pins pass DISTINCT values). No `PrincipalStore` composed in the correct build. |
| **(4) Satisfiability** | ✅ | correct build **76/76**; STUB **53 failed / 23 passed** behavioural RED@HEAD (imports resolve, `generate_audit_ddl()=''`, no collection error); w3 fold-guard **29 passed**; w2 shape-guard **56 passed**; ruff clean; mypy **Success: 231 source files**. `PrincipalStore.delete(email=...)` (the survives-delete pin's dependency) exists at HEAD — no C-DEF risk. |

**One honest observation (NOT a gap):** the offline schema field pin passes a text-valid computed/`<future>` field, so it does not by itself distinguish write-captured from derived — the discrimination lives entirely in the two behavioural pins (unseeded-principal capture + post-delete survival). Those are sound discriminators, and the engine cannot express a read-time-lazy field anyway, so there is no surviving lazy build. No missing pin.

**Release recommendation: SUFFICIENT — safe to release the builder** (fields + the 2 ruled tripwire edits close 61a). The §9 forensics property is genuinely pinned: identity is captured at write from caller input, stored as denormalized values, and provably outlives a hard actor-principal delete. Prior residual (append-faithful-clone routing) unchanged and non-blocking. The eventual build still gets its cold audit per CLAUDE.md.

_Round-2 (surface/ulid/routing) and Round-1 (original INSUFFICIENT) preserved below._

---

## ⭐ ROUND 2 RE-GRADE (2026-08-23, superseded by Round 3 above)

**VERDICT: CONTRACT SUFFICIENT.** The author's revision (68→71 pins) CLOSES both Round-1 blockers decisively and substantially closes the residual. Graded at the same tree state (`e92bd0f`, wave uncommitted; revised contract files re-synced into the provenance-asserted scratch `/tmp/lore-adv-61a-w4`, `loremaster.__file__` inside it). Every claim below is a wrong-build run against the REVISED contract, on the live store `ws://127.0.0.1:18000`.

| Delta the lead asked me to verify | Result | Receipt |
|---|---|---|
| **(1) MRO surface** — inherited mutator must red | ✅ **CLOSED** | Build B (`AuditStore(_Base)` w/ inherited `purge`) → allowlist pin + denylist pin **2 failed / 3 passed**. Pin uses `inspect.getmembers` over `__mro__` (resolved surface), allowlist-the-safe (`⊆ {append, append_fragment, ensure_ready, close}`). Self-mutation-proof pin `test_the_MRO_detector_sees_an_INHERITED_mutator` present (asserts detector sees inherited purge AND body-scan misses it). |
| **(1b) NOVEL-named inherited mutator** (`obliterate`) must red | ✅ **CLOSED** | Build B′ (inherited `obliterate`, NOT in `_FORBIDDEN_MUTATOR_NAMES`) → **allowlist pin RED**, denylist pin GREEN. Proves it is allowlist-the-safe over the resolved surface, NOT a forbidden-name blocklist. |
| **(2) ulid CREATION-ORDER** (not merely 26-char shape) | ✅ **CLOSED** | Build D (`uuid4` id) → `test_sequential_appends_produce_creation_ordered_ids` **RED** ("At index 1 diff"). Pin asserts `ids == sorted(ids)` + strictly-increasing (`itertools.pairwise`) with a 2 ms sleep forcing distinct ULID ms-timestamps — the ORDER property, not the shape. |
| **(3) fragment routing** — Build E must red (one path) | ⚠️ **SUBSTANTIALLY closed** | Build E2 (divergent params) → routing pin **RED**. Build E1 (**faithful byte-identical clone** — `append` hand-rolls the SAME statement text, never calls `append_fragment`) → routing pin **PASSES**. See the bound below. |
| **(4) Satisfiability** | ✅ | correct build **71/71** GREEN; STUB **48 failed / 23 passed** behavioural RED@HEAD (imports resolve, `generate_audit_ddl()=''`, no collection error); w3 fold-guard **29 passed**; w2 shape-guard **56 passed**; ruff clean; mypy clean (production code byte-identical to Round-1's `Success: 231 source files`). |

**The one precisely-stated residual bound (3) — why it does NOT block SUFFICIENT.** `test_append_write_IS_the_composable_fragment_one_path` is a statement-TEXT-equality check: it captures the statement `append` hands to `execute_transaction` and asserts it equals `compose(append_fragment(same args))`. This reds a DIVERGENT append (different params/structure, or a lax `.query()` — Build E2) and reds any clone **the moment `append_fragment` is edited** (the pin recomputes `append_fragment` live, so no silent drift is possible). It does NOT red a faithful byte-identical clone at ship time (Build E1). I judge this acceptable and NOT a blocker because: (a) the residual was LOW severity from Round 1 (both paths are independently behaviourally pinned); (b) E1 is behaviourally identical to the correct build; (c) E1 is drift-protected — it cannot diverge undetected; (d) the natural implementation (decision 1: `append = compose(self.append_fragment(...))`) is simpler than deliberately duplicating ~15 lines. **Optional airtight hardening (not required for release):** monkeypatch `store.append_fragment` to return a sentinel `TxnFragment` and assert `append` consumed it — that is a call-graph proof (routing-is-not-sharing gold standard) where the current pin is a text proxy. Offered so the operator can choose zero-tolerance on the one-path property; I do not gate release on it.

**Release recommendation: SUFFICIENT — safe to release the builder** (closes 61a). Both correctness/security blockers are closed; the sole remaining item is a contrived, drift-protected, behaviourally-identical DRY smell. Per CLAUDE.md, the eventual build still gets its cold audit; no contract revision skips the adversary (none is needed here).

_Round-1 report (the original INSUFFICIENT grade + full probe methodology) is preserved verbatim below for the record._

---

## SUMMARY BLOCK (ROUND 1 — historical; superseded by the Round-2 verdict above)
- **VERDICT: CONTRACT INSUFFICIENT** — 2 concrete missing pins (below). The contract is otherwise strong: satisfiable (68/68 on my independent correct build), RED-honest, quantifier-complete on the action domain, live-verified fold, both live guards green. These are ADDITIVE pins, not a rewrite.
- **P1 headline — did a wrong build survive?** YES, two: (D) a `uuid4` id (NOT a `ulid()`, not creation-ordered) passes ALL 24 store pins → the Fork-G-ruled `ulid` mint is UNPINNED; (B) an inherited public mutator (`AuditStore(_Base)` with `purge()`) passes ALL 4 append-only surface pins → the surface guard's reach is class-body-only, blind to the actual callable surface.
- **Graded:** e92bd0f · HEAD-at-report: e92bd0f · SAME. (Wave uncommitted; scratch copied from working tree at e92bd0f.)
- **Satisfiability:** 68/68 GREEN on my own correct reference build (live store `ws://127.0.0.1:18000`); `loremaster.__file__` = `/tmp/lore-adv-61a-w4/loremaster/loremaster/__init__.py` (#140 — inside scratch). ruff clean, mypy clean (231 files), w3 fold-guard 29✓, w2 shape-guard 56✓.
- **RED honesty (P7):** 46 failed / 22 passed against a behavioural STUB — imports all resolve (no collection error), matches the author's claim exactly.
- **Boundary (61a/61b):** HELD. No `requires_audit` / PDP-carve-out / `authorize` PIN in either file (only docstrings saying they are NOT pinned). No leak.
- **Author claims verified:** the `agent`-not-folded-but-sound fold is SOUND — proven LIVE (`test_the_full_generate_ddl_applies_with_audit_folded` GREEN: the whole folded `generate_ddl` with `record<agent>` over an absent `agent` table applies to a fresh 3.2.4 store).
- **Missing pins:** (1) append id is `ulid`-shaped / creation-ordered; (2) append-only surface over the RESOLVED (MRO) method set, not the class body.
- **Residuals (individual verdicts in §Residuals):** append not mutation-proven to route THROUGH append_fragment (E, confirmed); AST pins are `append`-body-scoped (over-constraint note, not a false-green); old→new omit-vs-null non-discrimination (non-finding, verified benign).
- **Packages considered:** none — no new mechanism specified. Agree with author: `ulid.ULID` (existing dep, `create_keep` precedent) + internal seams (`wrap_store_rejection`/`compose`/`execute_transaction`/`TxnFragment`); no library being hand-rolled.
- **Probe record:** §Probe record (every wrong build + command + real output). Scratch: `/tmp/lore-adv-61a-w4` (disposable `scratch_copy.sh`; safe to `rm -rf`).

---

## P1 — Wrong builds run against the REAL contract (the highest-value probe)

All builds run in a provenance-asserted scratch (`scratch_copy.sh`, `loremaster.__file__` INSIDE the copy) against the live 3.2.4 test store `ws://127.0.0.1:18000`. Each was restored to the correct build after.

| # | Wrong build | Contract result | Verdict |
|---|---|---|---|
| **A** (control) | a public `delete()` mutator on `AuditStore` | surface pins **2 failed / 2 passed** (RED) | surface pin **fires** on a body-defined mutator ✓ |
| **B** (reach) | `AuditStore(_AuditBase)`, `purge()` **inherited** | 4 surface pins **all GREEN** | ⛔ **SURVIVES** — reach gap (missing pin #2) |
| **C** (control) | action ASSERT **frozen at import** | derivation pin **1 failed** (RED) | mutation pin **fires** ✓ |
| **D** (id) | append id = `str(uuid4())` (not `ulid`) | store contract **24/24 GREEN** | ⛔ **SURVIVES** — `ulid` unpinned (missing pin #1) |
| **E** (DRY) | `append` hand-rolls its own CREATE (never calls `append_fragment`) | store contract **24/24 GREEN** | ⛔ **SURVIVES** — routing-through-fragment unpinned (residual) |

Two survivors are missing pins; E is a residual (both paths are behaviourally pinned, so a harmful divergence is hard but not impossible). A and C are positive controls proving the guards they exercise genuinely fire.

---

## MISSING PINS (the tests that should exist + the defects they catch)

### Missing pin #1 — the Fork-G-ruled `ulid()` id mint is UNPINNED  (severity: MEDIUM–HIGH)

**The defect it catches.** Fork G RULES the record id `= ulid()` — *"creation-ordered, sortable … NOT a counter-row or sequence mint"* — because an audit LOG's intrinsic value is append-ordered history (reconstructing the order of admin actions). The contract's own docstrings claim it (`test_two_appends_produce_DISTINCT_ids`: *"a build that reused one id (or a fixed id) is caught"*; `TestAppendDoesNotContendOnAHotRow`: *"a build that helpfully introduced a counter-row mint would contend"*). **But no ASSERTION pins the shape.** Build D (`str(uuid.uuid4())` — distinct, but random and NOT creation-ordered) passed all 24 store pins:

```
BUILD D: append id is uuid4, not ulid
24 passed in 1.57s
```

`test_two_appends_produce_DISTINCT_ids` only asserts `first != second`; `TestAppendDoesNotContendOnAHotRow` only asserts 8 distinct ids + 8 rows. A `uuid4` build satisfies both — and so would a *succeeding* counter-row mint (the finding mint demonstrably lands 8/8 at 8-way, so it produces 8 distinct ids + 8 rows and passes the "no contention" pin **for a fixture reason**, not because it doesn't contend). This is the PKT-28 C1 pattern twice over: prose describing behaviour no assertion checks, and a fixture named for a hazard that passes without exhibiting it. A builder shipping random ids silently loses the append-ordering Fork G bought.

**The test that should exist** (either form):
- `test_append_id_is_ulid_shaped`: `_bare(await store.append(...))` matches the 26-char Crockford base32 ULID shape (`^[0-7][0-9A-HJKMNP-TV-Z]{25}$`); OR
- `test_sequential_appends_yield_lexicographically_ordered_ids`: for ids minted in creation order `id_1 < id_2 < id_3` as strings (the property Fork G actually needs — creation-order == id-order). This form also kills a store-random-id build and a counter-mint whose numeric ids aren't zero-padded.

### Missing pin #2 — the append-only surface guard misses INHERITED mutators (severity: MEDIUM; security-boundary reach gap)

**The defect it catches.** `_auditstore_public_methods()` (the reach for BOTH `TestTheAppendOnlySurfaceLayer1` and the born-wrapped/txn AST pins) walks only the `AuditStore` **class body** (`node.name == "AuditStore"` → `cls.body`). A public mutator inherited from a base class is invisible. Build B proved it — `purge()` is callable on every `AuditStore` instance, yet all 4 surface pins pass:

```
purge on class -> True
purge is inherited (not in AuditStore.__dict__) -> True
BUILD B: surface pins:  4 passed in 0.14s
```

The append-only surface is a SECURITY boundary (Fork G threat model: a compromised admin cannot erase/rewrite the trail). Its guard's REACH is a hidden constant — *"methods textually in the class body"* — not the property it means to enforce — *"methods callable on an `AuditStore` instance"* (#344/#345, INSTRUMENT-0: reach must be DERIVED from production truth and coverage a checked variable). The mirror (`KeepStore`) has no base today, so this is off the default path — but a plausible future refactor hoisting the shared lifecycle (`_ensure_connection`/`ensure_ready`/`close`, identical across Principal/Keep/Audit stores) into a base could carry a mutator, and the guard would never see it.

**The test that should exist** (either form):
- reach over the RESOLVED surface: build the public set from the instance/MRO, e.g. `{n for n in dir(AuditStore) if not n.startswith("_") and callable(getattr(AuditStore, n))}` (minus a `{}`-empty `object` baseline), and apply the same allowlist — then Build B reds; OR
- a structural invariant pinning the reach to equal the body scan: `assert AuditStore.__bases__ == (object,)` ("`AuditStore` inherits nothing — mirror `KeepStore` — so the class-body scan IS the full surface; if you add a base, widen the surface scan and say so").

---

## P1b — QUANTIFIER TABLE (∀-over-inputs vs guarded-by-failure-mode)

| Invariant | Class | Receipt |
|---|---|---|
| `action` domain = exactly `{WRITE,DELETE,SET_SCOPE,SET_OWNER}` | ∀ (set equality) | `test_the_ruled_action_domain_is_EXACTLY_the_mutating_actions` catches BOTH widen and narrow; live `test_a_plausible_but_unaudited_action_is_rejected` (READ) + `_a_garbage_action` + positive control `_every_audited_action_is_accepted`. No door left. |
| `action` ASSERT derived at CALL time from `_AUDITED_ACTIONS` | ∀ (mutation) | Build C (freeze at import) → `test_changing_the_AUDITED_ACTIONS_tuple_changes_the_emitted_ASSERT` RED. Fires. |
| READ never audited | ∀ | `test_READ_is_NOT_an_audited_action` + live rejection. |
| every audited action reaches the DDL | ∀ | `test_every_audited_action_reaches_the_ddl` (membership) alongside the exact-set pin. |
| old→new capture (WRITE old+new; DELETE new=None; SET_OWNER change) | ∀ over the 3 fate shapes | distinct fixture values per shape ⇒ swap/drop-old/drop-new each fail (verified §Fixtures). Both `option<>` directions exercised. |
| required-field discipline (5 required fields) | ∀ (parametrized ∀-omit) | `test_a_row_missing_a_required_field_is_rejected` over `{action, actor_principal, actor_agent, target_table, target_row}` + all-present positive control. Discriminates any one accidentally `option<>`. |
| FLEXIBLE arbitrary-shape round-trip | ∀ (hostile nested fixture) | `test_old_and_new_value_round_trip_an_ARBITRARY_nested_shape` (nested objects/lists/undeclared keys). |
| atomicity (co-producer rejected ⇒ audit append rolls back) | guarded → **covered** | NEGATIVE pin uses `append_fragment` directly; discrimination rests on `append_fragment` being envelope-free single-statement, which IS separately pinned (`test_append_fragment_returns_a_single_statement_create_fragment`). Positive control lands both. No unguarded door found. |
| born-wrapped taxonomy (raw→domain; transport passthrough) | ∀ over `{store-error, connection, contention}` | fault-injection over all three + real-rejection behavioural leg; the passthrough discriminator reds a catch-all wrong wrap. |
| **id is `ulid`/creation-ordered** | **UNGUARDED** | ⛔ **missing pin #1** — Build D (uuid4) walks the "distinct id" outcome through a non-ulid door; distinctness+count pins engage but the shape/order property has NO pin. |

---

## P1c — REACH TABLE (every guard the contract introduces/relies on)

Legs: **E** = empirical wrong-build in scratch; **C** = construction-inspection.

| Guard | Reach DERIVED vs hand-list | Coverage a checked var? | Effect vs proxy | One-source / mutation-proven | Verdict |
|---|---|---|---|---|---|
| append-only surface scan `_auditstore_public_methods` | DERIVED (AST) **but over class BODY only** — misses MRO | NO for inherited members | proxy (textual body ≠ callable surface) | allowlist-the-safe ✓ (names it does see) | ⛔ **MISSING PIN #2** (E: Build B survives) |
| `action` ASSERT derivation | DERIVED from `_AUDITED_ACTIONS` at call time | YES (exact-set + membership) | effect (emitted DDL) | mutation-proven (Build C reds) | SAFE (E) |
| `_define_field` / `_define_table` routing | n/a (routing proof) | — | effect (COMMENT probe in emitted DDL) | mutation-proven (`_ROUTES_THROUGH_the_shared_field_emitter` / `_uses_the_shared_define_table_emitter`) | SAFE (C) |
| fold both-paths equality | DERIVED (one emitter `_audit_statements`, both paths) | YES (set equality reds on divergence) | effect (emitted field set) | one emitter consumed twice | SAFE (C) |
| fold-into-`generate_ddl` + position | DERIVED (AST/string over emitted DDL) | — | effect (live: `TestTheFullDdlWithAuditFoldedApplies`) | — | SAFE (E — live-verified) |
| w3 fold-coverage guard (external, relied on) | DERIVED (AST over `_*_statements`) | YES | effect | — | SAFE — 29✓ with audit slice folded |
| born-wrapped `wrap_store_rejection`-in-`append` AST | append body only | — | proxy (name present) — **but** behavioural legs (raw→AuditStoreError, transport passthrough) observe EFFECT | + external w2 module-sweep 56✓ | SAFE (belt-and-braces) |
| `execute_transaction`-in-`append` AST | append body only | — | proxy (name present) | atomicity effect via `append_fragment` | SAFE, but see residual E (append not proven to CONSUME append_fragment) |

---

## Fixture-discrimination verdicts (P2)

- **old→new shapes DISCRIMINATE.** WRITE `old={"status":"open"}`/`new={"status":"done"}`, DELETE `old={"body":"gone"}`/`new=None`, SET_OWNER bob→carol — distinct values per shape, so a swap, a drop-old, or a drop-new each fails a specific assertion. Both `option<>` directions (CREATE-none-old, DELETE-none-new) are exercised — the discrimination the DELETE pin needs is present. ✓
- **Required-field ∀-omit DISCRIMINATES** any single field made accidentally `option<>`, with the all-present positive control proving the omission pins fail for the right reason (a missing field, not a broken write). ✓
- **Action monoculture AVOIDED.** Fixtures use WRITE/DELETE/SET_OWNER/SET_SCOPE and negative READ/garbage — no single-value monoculture; a build branching on one action value cannot hide. ✓
- **`ulid` fixture does NOT discriminate** (missing pin #1): `test_two_appends_produce_DISTINCT_ids` at N=2 with only `!=` cannot tell ulid from uuid4 from a store-random id — the blinding perturbation is "swap the mint for any distinct-id source" and it stays green (Build D, proven on the correct oracle: the SAME pin is green on my ulid build too).
- **Threat-model pins are prose (acknowledged KNOWN BOUND).** They check the load-bearing concepts (`append-only`, `in-process`, `root`/`direct-store`, `version b`) are present, not exact wording. Correctly labelled; not a false-green (a build omitting the concepts reds).

---

## Reproduced receipts

- **Satisfiability (correct reference build):** `68 passed in 4.50s`; `loremaster.__file__ = /tmp/lore-adv-61a-w4/loremaster/loremaster/__init__.py`. No C-DEF class defect (no pin red on a correct build). Harder legs: `ruff … All checks passed!`, `mypy loremaster … Success: no issues found in 231 source files`.
- **RED honesty (P7):** STUB (`_audit_statements`→`[]`, `generate_audit_ddl`→`""`, `append`/`append_fragment`→`NotImplementedError`) → `46 failed, 22 passed`, imports resolve (`generate_audit_ddl()=''`), no collection error. Behavioural RED, exactly the author's counts.
- **Live guards with audit added:** w3 `test_schema_fold_coverage.py` `29 passed`; w2 `test_engine_rejection_seam.py` `56 passed`. Both the author's counts reproduced.
- **`agent`-not-folded-but-sound (author flag) VERIFIED LIVE:** the full folded `generate_ddl` (emitting `actor_agent record<agent>` while the `agent` table is NOT emitted by `generate_ddl`) applies to a fresh 3.2.4 store and creates the `audit` table — `TestTheFullDdlWithAuditFoldedApplies` GREEN. A `record<t>` field-def needs no target table at DDL time. The flag's imprecise half ("agent defined earlier") is correctly identified; the load-bearing fact (record-link-needs-no-target) is proven, not asserted.
- **Boundary:** grep for `requires_audit|authorize|carve|Decision` in both files → only DOCSTRINGS declaring them out of scope; zero pins. 61a/61b boundary held.

---

## Residuals (each with an individual verdict)

1. **`append` is not mutation-proven to route THROUGH `append_fragment` (Build E — CONFIRMED).** `append` hand-rolling a parallel CREATE (never calling `append_fragment`) passes 24/24. Decision (1) intends `append = compose(self.append_fragment(...))` so 63/64 (which use `append_fragment`) and direct `append` callers cannot diverge. **Verdict: residual, worth a cheap pin.** Both paths are independently behaviourally pinned (a harmful divergence must keep BOTH correct), so severity is low — but a one-line AST/mutation pin (`append` references `append_fragment`; or perturb `append_fragment` and require `append`'s emitted statement to move) would close the DRY gap and matches the "one emitter" intent.
2. **The `append`-scoped AST pins are OVER-CONSTRAINED, not under (note, not a false-green).** `test_append_executes_via_the_verified_transaction_seam` and `test_append_routes_through_the_shared_wrap_seam` walk only the `append` FunctionDef body; a correct build delegating the txn/wrap to a private helper would false-RED. **Verdict: satisfiable (the reference build inlines both), but flag for the builder** — keep `execute_transaction` + `wrap_store_rejection` referenced directly in `append`, or these pins trap a clean refactor. This is the mirror risk of missing pin #2's reach (body-only) pointing the other way.
3. **old→new "omit-when-None" vs "always write, binding None" is non-discriminating — VERIFIED BENIGN.** Under an explicit projection both decode to `None` (store §2), so the observable behaviour is identical; there is nothing to discriminate. **Verdict: non-finding.**
4. **`_count` returns 0 on any exception (store test helper).** Tolerant-of-absent-table by design; `before`/`after` are both measured on the same table so a real leak still moves the count. **Verdict: non-finding.**

---

## Probe record (commands + real output)

Scratch built with `./scripts/scratch_copy.sh /tmp/lore-adv-61a-w4` (excludes poison, `uv sync --all-packages`, asserts provenance). Correct reference build authored independently (`audit.py` + `surreal_schema.py` additions mirroring `_keep_statements`/`create_keep`), snapshotted, then each wrong build patched → run → restored.

**Reference-build emitted audit DDL (independently authored, matches the field set Fork G rules):**
```
DEFINE TABLE IF NOT EXISTS audit SCHEMAFULL
DEFINE FIELD OVERWRITE actor_principal ON audit TYPE record<principal>
DEFINE FIELD OVERWRITE actor_agent ON audit TYPE record<agent>
DEFINE FIELD OVERWRITE target_table ON audit TYPE string ASSERT string::len(string::trim($value)) > 0
DEFINE FIELD OVERWRITE target_row ON audit TYPE string ASSERT string::len(string::trim($value)) > 0
DEFINE FIELD OVERWRITE old_value ON audit TYPE option<object> FLEXIBLE
DEFINE FIELD OVERWRITE new_value ON audit TYPE option<object> FLEXIBLE
DEFINE FIELD OVERWRITE created_at ON audit TYPE datetime DEFAULT time::now()
DEFINE FIELD OVERWRITE action ON audit TYPE string ASSERT $value IN ['WRITE', 'DELETE', 'SET_SCOPE', 'SET_OWNER']
```

**A (control):** added `async def delete` → `TestTheAppendOnlySurfaceLayer1`: `2 failed, 2 passed` (allowlist + denylist pins fire).
**B (reach):** `AuditStore(_AuditBase)` inherited `purge()` → `hasattr(AuditStore,'purge')=True`, `'purge' not in AuditStore.__dict__=True`; surface pins `4 passed` → **survives**.
**C (control):** action ASSERT frozen at import → `test_changing_the_AUDITED_ACTIONS_tuple_changes_the_emitted_ASSERT`: `1 failed, 4 passed` (mutation pin fires).
**D (id):** `str(uuid4())` id → `test_audit_store.py`: `24 passed` → **survives** (ulid unpinned).
**E (DRY):** `append` hand-rolls CREATE, never calls `append_fragment` → `test_audit_store.py`: `24 passed` → **survives** (routing unpinned).

---

## VERDICT: CONTRACT INSUFFICIENT

Two concrete missing pins, each with a surviving wrong build:
1. **The `ulid()` mint is unpinned** — a random/non-ordered id passes the whole store contract, defeating Fork G's ruled append-ordering property (add an id-shape or lexicographic-order pin).
2. **The append-only surface guard's reach is class-body-only** — an inherited mutator is invisible on a security boundary (scan the resolved surface, or pin no base class).

Plus one residual worth a cheap pin (append→append_fragment routing) and one builder-facing over-constraint note. Everything else is strong and verified: satisfiable, RED-honest, quantifier-complete on the action domain, fold live-verified, both live guards green, and the 61a/61b boundary held. Fix the two pins and re-run the adversary on the delta (no revision skips the adversary — CLAUDE.md).
