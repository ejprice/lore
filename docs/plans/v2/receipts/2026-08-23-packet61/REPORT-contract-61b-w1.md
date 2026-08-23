# REPORT — contract-61b-w1 (the PDP CORE contract)

brief-base v14 read · brief project v7 read

**State:** done (RED contract shipped; lead-61's D1–D4 rulings, the adversary's F1/F2/F3 fixes, AND
the security-auditor/cold-audit round — #416 MEDIUM + F2/F3/F4/R4 LOW — all applied; satisfiability
+ 9 mutation receipts green). Node counts: **123 pins** — 102 pure
(`lorerunes/tests/test_pdp_core.py`, of which 3 are the charter STANDING INVARIANTS, green at HEAD) +
21 live-store oracle (`loremaster/tests/test_pdp_oracle_61b.py`). ⚠ Two rounds used overlapping
F-numbers; the security round's are labelled "SEC-" below to disambiguate from the adversary's.
**Deviations (one line each):**
- **F3 (adversary, ruled by the sidecar) corrects Fork D:** `Subject`/`Resource`/`Decision` are
  STDLIB frozen dataclasses (`@dataclass(frozen=True, slots=True)` + `__post_init__`), NOT pydantic —
  lorerunes is stdlib-only (`deps==[]`). My earlier pydantic reference violated the charter (it only
  "worked" because the shared venv has pydantic). Added the CHARTER PIN (every lorerunes import ∈
  `sys.stdlib_module_names ∪ {lorerunes}` + `deps==[]`).
- The design's Fork-D-vs-Fork-G inconsistency (Resource 3 fields vs the carve-out needing a table)
  was RESOLVED as reading **B2** — lead-61 CONFIRMED it (finding #414). Forward-note #415 added.
- SET_SCOPE required a signature reconciliation: D1 confirmed a 3-POSITIONAL-arg `authorize`, while
  D4(b) needs a target scope — resolved as a **keyword-only `target_scope`** (defaults `None`,
  required only for SET_SCOPE), preserving the 3 positional args. Flagged below to confirm.
**Packages considered:** `pycasbin` → **bespoke** (design §11 ruled it out — split-brain, no live-store
oracle; cited, not re-derived). `pydantic` → **REUSED** (the frozen `extra="forbid"` value-object idiom,
read from `principals.Principal`/`keeps.Keep`). No mechanism hand-rolled.
**Reuse ledger:** the contract adds only TEST helpers. The EXPLAIN plan-walker
(`_operators`/`_scans_table`) — **HAND-ROLLED (re-expressed), cited**: the shipped
`test_keeps_schema.TestTheKeeperIndexFires` + `scripts/probe_read_filter_61b.py` both hand-roll the
identical walker (test-instrument parsing, not production policy — the probe precedent). The D2 AST
helper `_module_binds_name_by_import_from` and the F3 charter scanner (`_lorerunes_modules` + the
stdlib-import walk) — **HAND-ROLLED** (bespoke source-inspection guards; no existing helper checks
import-vs-assign or a stdlib-only charter). Production PDP symbols are the builder's.
**Graded:** N/A — a RED contract renders no verdict on another artifact. Authored/updated at HEAD `599354a`.
**Decisions needed (for lead-61 / adversary / operator):**
1. **CONFIRM the D1×D4(b) signature reconciliation:** `authorize(subject, action, resource, *, target_scope=None)`
   and `authorize_filter(subject, action, table, *, target_scope=None)` — 3 positional args (D1) + a
   keyword-only target for SET_SCOPE (D4(b)). This is the only place the two rulings interact.
2. **Naming:** lead wrote `ROLE_MEMBER`/`ROLE_ADMIN`; I pinned `PRINCIPAL_ROLE_MEMBER`/`PRINCIPAL_ROLE_ADMIN`
   (+ `PRINCIPAL_ROLES`) — unambiguously principal-specific (the "do NOT merge with agent.role"
   annotation) AND matching surreal_schema's existing `_PRINCIPAL_ROLE_*` convention. Flip if you want
   the shorter names (trivial rename; the builder must match).
3. **Observation (D4(a) CONFIRMED, pinned):** DELETE/SET_SCOPE are owner-gated, scope-INDEPENDENT — an
   owner can DELETE a `keep:<id>` row of a keep they've LEFT (r11). Pinned with the "ownership≠scope"
   note; no action needed.

## Receipt pointers (section — never re-pasted)
- The pins: `lorerunes/tests/test_pdp_core.py` (86, pure) + `loremaster/tests/test_pdp_oracle_61b.py`
  (16, live-store). Node ids: `--collect-only -q` on each.
- Satisfiability + 4 mutation receipts: §"Satisfiability receipt" + §"Mutation proofs" below.
- The lead's D1–D4 rulings applied: §"Lead rulings applied" below.
- Findings: #414 (Fork-D/Fork-G carve-out inconsistency, ruled B2, CONFIRMED) · #415 forward-note
  (Resource.table derived-not-supplied at 63/64) is captured as a code comment (test_pdp_core.py header).

## What this wave is (61b-w1) and what it is NOT

61b-w1 is the **PDP CORE** — the in-process single-brain authorization engine, in `lorerunes`
(stdlib-only): the predicate IR + two total interpreters + `Action`/`Subject`/`Resource`/`Decision` +
per-action predicates + `authorize`/`authorize_filter` + the admin short-circuit + the audit-obligation
flag + the LIVE-STORE ORACLE. Boundaries respected (I did not over-reach):
- **NOT touched:** `get_access_token`/`AccessToken`, credential minting/binding (packet 62 populates
  `Subject`; I DEFINE + CONSUME its shape). `Subject.visible_keep_ids` is INPUT here — the Fork-F
  resolver is **61b-w2**; my fixtures PROVIDE the keep set.
- **NOT touched:** any populated governed table — no owner/scope column added, no row migrated, no verb
  wired (63/64). Pinned against a SYNTHETIC `gov` table + FIXTURE `Resource`s + a synthetic `audit` table.
- **Fork K confirmed:** 61b-w1 ships NO `lore-adm` CLI verb touching the `run_query` stderr seam, so
  #401 stays deferred with its intact trigger.

## Lead rulings applied (D1–D4)

- **D1 (#414) → B2 CONFIRMED, no signature change.** `Resource` carries `table` (4 fields); `authorize`
  stays 3-positional; `authorize_filter(subject, action, table)`. The equivalence is STRUCTURAL:
  `authorize(s,a,r) == authorize_filter(s,a,r.table).matches(r)` — same table by construction. **#415
  forward-note added** (a comment, not a 61b pin): at 63/64, `Resource.table` is DERIVED from the row
  id, NEVER caller-supplied (a forged table would bypass the carve-out — anti-injection §3.2.2).
- **D2 → RE-HOME (my earlier drift cross-check REPLACED).** The principal role domain + `AUDIT_TABLE`
  are homed in stdlib-only `lorerunes` (`PRINCIPAL_ROLES`/`PRINCIPAL_ROLE_MEMBER`/`PRINCIPAL_ROLE_ADMIN`
  — principal-specific, NOT merged with agent.role/rank; `AUDIT_TABLE`), and `surreal_schema` IMPORTS
  them. Pinned by SHARING (a private copy REDS), two guards keyed to the type:
  `TestSharedVocabularyIsReHomedInLorerunes` — (a) `_PRINCIPAL_ROLES` is the SAME OBJECT
  (identity — reliable for a tuple; a private copy is a different object → RED); (b) `AUDIT_TABLE`
  IMPORTED-not-assigned via an AST source guard (interning-proof — `is` cannot tell a private `"audit"`
  from the shared one; measured: the AST guard caught it, `is` would not). The `_AUDITED_ACTIONS`
  cross-check stays `==` (that domain is NOT re-homed — a must-AGREE check across two vocabularies).
- **D4(a) → CONFIRMED, PINNED with a note.** DELETE/SET_SCOPE owner-gated, scope-INDEPENDENT; the
  "ownership≠scope; adding a household conjunct breaks owner-cleanup" note is on `TestDeletePredicate`.
- **D4(b) → SECURITY REFINEMENT applied.** SET_SCOPE = `owner=me AND target-scope-grantable`
  (§3.2.3/§4.3): a member re-scopes their own row to a keep ONLY IF a member of it; freely to private +
  server. `authorize`/`authorize_filter` take keyword-only `target_scope`; the member SET_SCOPE
  predicate is `owner_me` if grantable else `NoRows`. `TestSetScopePredicate` covers grantable
  (owner rows), non-grantable keep (NoRows over the whole table), the discriminating own-row fixture
  (own row → keep-not-in REFUSED / keep-in allowed), and no-target (grants nothing). The oracle covers
  SET_SCOPE with grantable + non-grantable targets.

## Adversary fixes applied (F1 / F2 / F3) — verdict was INSUFFICIENT, contract otherwise STRONG

- **F3 (ruled by the sidecar — Fork B/D addendum) → stdlib dataclasses + a charter pin.** See the
  first deviation above. `Subject`/`Resource`/`Decision` are now `@dataclass(frozen=True, slots=True)`
  (frozen = immutable; slots = the `extra='forbid'` equivalent — unknown kwargs raise, no extra attrs;
  `__post_init__` = the domain validation). The value-object pins assert BEHAVIOUR, so they held across
  the switch unchanged. **`TestLorerunesStdlibOnlyCharter`** (reach law on the charter — NOTHING
  guarded it before): every TOP-LEVEL import in EVERY lorerunes module ∈ `sys.stdlib_module_names ∪
  {lorerunes}` (the stdlib set DERIVED from the interpreter, never a hand-list), module set derived
  from the package dir (coverage-checked), + `pyproject deps == []`. These 3 are STANDING INVARIANTS
  (green at HEAD — lorerunes is already clean), mutation-proven (M6).
- **F1 → the #413 IN-expansion is now STORE-tested at ≥2 keeps.** The old emitter pin used a 1-keep
  subject, where a 1-element `IN` IndexScans, so the expansion was INERT (couldn't discriminate the
  expanded OR from a literal IN). Added `_two_keep_member` (keeps={k1,k9}) to the oracle's
  `_all_subjects` AND to `test_member_read_emitter_with_TWO_keeps_indexscans_no_tablescan`: the
  expanded `scope=$k0 OR scope=$k1` EXPLAINs IndexScan on the live store, while the literal 2-element
  `IN`-inside-OR control TableScans (`test_positive_control_literal_IN_inside_OR_tablescans`).
- **F2 (blocker — Fork-G single-brain) → admin SET_SCOPE audit + requires_audit-shares-member.** Added
  `test_admin_set_scope_into_a_non_grantable_keep_is_audited` (admin re-scoping its OWN row into a keep
  it is NOT in is a load-bearing bypass a member couldn't do → `requires_audit=True`) + the grantable
  discriminator (admin IN the keep → `False`). Mutation-proven (M5): a `requires_audit` computed from a
  member predicate that DROPPED grantability under-audits it and reds the pin — proving requires_audit
  SHARES the SAME member predicate `authorize` uses (ROUTING-IS-NOT-SHARING).

## Security-auditor + cold-audit fixes: #416 (MEDIUM) + SEC-F2/F3/F4/R4 (LOW)

- **#416 (MEDIUM — a latent cross-principal LEAK in the PUBLIC IR).** `ScopeInKeeps.to_surql`
  emitting UNPARENTHESISED disjuncts (`scope=$k0 OR scope=$k1`) is safe ONLY as a direct top-level
  Or child; under an And (`(owner=$p AND scope=$k0 OR scope=$k1)`) the 2nd disjunct ESCAPES (SQL
  binds AND tighter than OR) → returns OTHER principals' rows. Not reachable via 61b's entry points,
  but And/Or/ScopeInKeeps are re-exported and 63/64 compose them. RULING (option a): every node emits
  a SELF-CONTAINED (parenthesised) fragment. PINS: (1) **structural** —
  `TestPredicateFragmentsAreSelfContained`: no concrete node's `to_surql` has a top-level ` OR `
  outside parens (reach-law coverage); (2) **live-store composition-safety** —
  `TestCompositionSafetyNoLeakUnderAnd`: `And(OwnerPrincipalEq(alice), ScopeInKeeps({k1,k9}))` returns
  ONLY alice's rows ({r9,r11}), with the unparenthesised twin as a positive control that leaks r12
  (bob's). Mutation M7: unparenthesise ScopeInKeeps → both pins RED, leaking r12, **while the
  entry-point oracle stays GREEN** — the exact reason the oracle alone missed it. Index re-probe: the
  parenthesised ScopeInKeeps still IndexScans as a top-level READ disjunct (the 2-keep emitter pin);
  the under-And plan (`A AND (scope=$k0 OR $k1)`) is a **63/64 PERF note**, not a 61 pin — safety is
  fixed by the parens regardless of the plan.
- **SEC-F2 (LOW) — option<> absent-owner coverage.** The oracle's `gov` owners are now
  `option<record<>>` with NONE-owner rows (r13 server, r14 agent-private) seeded; the read path
  tolerates absence — `Resource.owner_*` is `str | None`, `matches` treats None as owned-by-nobody,
  and `to_surql` (store NULL) agrees (`TestAbsentOwnerRowsAgree`). The 2-keep emitter still IndexScans
  over the option<> column (no regression).
- **SEC-F3 (LOW) — confused-deputy hardening.** `Subject.__post_init__` rejects empty
  `principal_id`/`agent_id`; `Resource.__post_init__` rejects an empty owner WHEN PRESENT (None still
  allowed — that is SEC-F2's absent owner). Pins added to the value-object classes.
- **SEC-F4 (LOW — reach law) — derived mutating set.** `_MUTATING = frozenset(Action) - {READ}`
  (derived, not a hand-list), so a new mutating action auto-audits. `TestMutatingActionsAreDerived`
  pins it ∀ over `Action`; mutation M8: a hand-list that forgets SET_OWNER → RED. The
  `== _AUDITED_ACTIONS` cross-check now has teeth (the PDP side being derived catches a schema
  hand-list that forgot a new action).
- **SEC-R4 (LOW — DRY, D2 extended).** `PRINCIPAL_TABLE`/`AGENT_TABLE` are homed in lorerunes and
  IMPORTED by surreal_schema (was a 2nd copy in the emitter). Pinned by the same AST
  import-not-assigned guard as AUDIT_TABLE (`test_governed_table_names_are_imported_from_lorerunes`);
  mutation M9: a private copy → RED.

## The mechanism (Fork A) + per-action predicates (Fork C)

Closed IR (`ScopeEq`, `OwnerPrincipalEq`, `OwnerAgentEq`, `ScopeInKeeps`, `And`, `Or`, `AllRows`,
`NoRows`); two total interpreters over one tree (`to_surql` bound params + `matches`). Member
predicates: READ = `(agent-private∧owner=(p,a)) ∨ (principal-private∧owner_principal=p) ∨ server ∨
scope∈keeps`; WRITE = same private clauses with EXACT `(p,a)` (reading 1) ∨ `scope∈keeps` ∨
`(server∧owner=(p,a))`; DELETE = `owner=(p,a)` (any scope); SET_SCOPE = `owner=(p,a) ∧ grantable(target)`;
SET_OWNER = `NoRows`. Admin ⇒ `AllRows` except the audit carve-out (`NoRows` for the 4 mutating actions
on the audit table). `requires_audit = allowed ∧ admin ∧ action∈mutating ∧ ¬member_predicate.matches`
— fires IFF the admin bypass was load-bearing (own-row admin write → False; cross-owner → True;
SET_OWNER always True; READ never audited — restricted to the `_AUDITED_ACTIONS` domain).

## The live-store ORACLE (the packet's trust anchor)

`TestTheLiveStoreOracle` — for a HOSTILE 12-row fixture (2 principals × 2 agents, EVERY scope, keep
rows in/out of `$my_keeps`, server rows, empty-keeps subject) × every `(subject, action)`, asserts
BYTE-IDENTICAL id sets: `{authorize allowed}` == `store SELECT id FROM gov WHERE
authorize_filter(...).to_surql()` against the REAL 3.2.4 store — NEVER a mock (the mock IS the
false-clear). Separate indexes on `scope`/`owner_principal`/`owner_agent` (probe E2). Plus the
SET_SCOPE oracle (grantable/non-grantable) and the carve-out oracle (`WHERE false` selects 0 audit
rows, matching the Python DENY; admin READ selects all).

## Emitter shape (finding #413 / store-ref §2) — pinned live

`TestTheReadEmitterIndexScans`: the member READ emitter EXPANDS `scope IN $my_keeps` to per-keep
equality disjuncts and binds owners as `type::record('principal', $p)` (bare-string param — stdlib-only
lorerunes) → IndexScan, NO TableScan of `gov`. Positive controls: an unindexed predicate TableScans;
a literal `scope IN $set` inside an OR TableScans (the #413 trap the expansion avoids). De-risked live
before pinning (`/tmp/derisk_typerecord_61b.py`, throwaway; durable pins in the oracle).

## Coverage-as-checked-variable (reach law #344/#345)

`TestThePredicateIRIsAClosedAlgebra` DERIVES the concrete `Predicate` subclass set (not a hand-list),
asserts both interpreters are abstract on the base (a node missing either can't instantiate), the
derived set is non-empty (guard the guard), every node has a working `to_surql`+`matches`, and no
subclass is partially-abstract. A NEW node grows the set and reds a pin until both interpreters handle it.

## Satisfiability receipt

Built a known-correct reference PDP in a provenance-asserting scratch
(`./scripts/scratch_copy.sh --force /tmp/lore-scratch-61bw1`), re-homed the vocab in the scratch's
`surreal_schema` (the builder does this in the real tree — pre-authorized, its own commit), and ran the
full contract:

```
PROVENANCE (#140 — runs its OWN code):
  lorerunes  __file__ = /tmp/lore-scratch-61bw1/lorerunes/lorerunes/__init__.py
  loremaster __file__ = /tmp/lore-scratch-61bw1/loremaster/loremaster/__init__.py
  re-home identity: surreal_schema._PRINCIPAL_ROLES is lorerunes.PRINCIPAL_ROLES == True
                    surreal_schema.PRINCIPAL_TABLE is lorerunes.PRINCIPAL_TABLE == True (R4)
  reference PDP: stdlib @dataclass (NO pydantic import — charter clean); ScopeInKeeps parenthesised

123 passed (102 pure-core + 21 live-store oracle) against the STDLIB-DATACLASS reference build.
ruff check           : All checks passed! (both test files + pdp.py)
mypy lorerunes       : Success (12 source files — pdp.py + test_pdp_core.py)
mypy oracle file     : Success (no issues)
registration_sites.py: the PDP is NEW API within the EXISTING lorerunes MEMBER (not a new
                       member) → only the lorerunes/__init__.py re-export applies; no new
                       [tool.uv.workspace]/mypy_path/Containerfile registration owed. (The D2
                       re-home makes surreal_schema import from lorerunes — an existing edge.)
```

RED baseline (real tree, PDP unbuilt): pure-core **99 failed** via clean `pytest.fail` (finding #133
gate — no ImportError, no collection error) **+ 3 charter STANDING INVARIANTS green at HEAD** (they
scan the already-clean lorerunes modules — invariant guards, not build-gated, like the exact-set
registration pins); oracle 21 collected on the `_pdp` gate. Total 123.

## Mutation proofs (fixtures-must-discriminate)

- **M1 — divergence:** inverted `ScopeEq.matches` (to_surql unchanged) → the live-store oracle **REDS**.
  Proves the oracle catches a `to_surql`/`matches` split-brain a mock would hide.
- **M2 — wrong shared predicate:** dropped `ScopeEq(server)` from the READ builder →
  `test_member_read_visible_set` (correctness) **REDS** (r7/r8 lost), while the single-brain identity
  pin AND the oracle **STAY GREEN** — both interpreters moved together (sharing intact); the two legs
  (agreement vs value) are each necessary.
- **M3 — partial-abstract node (reach law):** added `_PartialNode(Predicate)` implementing only
  `matches` → `test_no_predicate_subclass_is_partially_abstract` **REDS**.
- **M4 — D2 private copy (mutation across the boundary):** added a private `_PRINCIPAL_ROLES` +
  `AUDIT_TABLE` shadowing the re-home in `surreal_schema` → BOTH sharing pins **RED** (the identity pin
  on the tuple; the AST guard on the string — which caught the private `"audit"` that `is` would have
  missed to interning). Proves the re-home is shared, not cloned.
- **M5 — F2 requires_audit-shares-member:** computed `requires_audit` from a member predicate that
  DROPPED grantability (a clone) → `test_admin_set_scope_into_a_non_grantable_keep_is_audited` **RED**
  (`requires_audit=False` where it must be True — under-auditing the admin bypass); the grantable
  discriminator stayed green. Proves requires_audit shares the real member predicate (single-brain).
- **M6 — F3 charter:** injected `import pydantic` into a lorerunes module →
  `test_every_lorerunes_module_imports_only_stdlib_or_itself` **RED**, naming the offender
  (`{'blankness.py': {'pydantic'}}`); the other 2 charter pins stayed green.
- **M7 — #416 composition leak:** unparenthesised `ScopeInKeeps.to_surql` → the structural pins AND
  the live-store composition-safety pin **RED** (leaked r12, bob's row), **while the entry-point
  oracle stayed GREEN** — proving the composition-safety pin catches the latent public-IR leak the
  oracle cannot see.
- **M8 — SEC-F4 derived mutating set:** hand-listed `_MUTATING` that forgot SET_OWNER →
  `test_every_non_read_action_is_treated_as_mutating` **RED** (SET_OWNER no longer audited).
- **M9 — SEC-R4 private table copy:** a private `PRINCIPAL_TABLE = "principal"` shadowing the
  re-home → the R4 sharing pin **RED** (AST assigned=True).

## Declared node ids
- Real tree (PDP unbuilt): 99 `lorerunes/tests/test_pdp_core.py::*` RED via the `_pdp` gate + 3
  `TestLorerunesStdlibOnlyCharter::*` GREEN (standing invariants) + 21
  `loremaster/tests/test_pdp_oracle_61b.py::*` RED (`--collect-only -q`; 123 total).
- GREEN-on-reference (scratch, stdlib-dataclass + re-homed): the same 123.

## Loose ends for the lead
- **Scratch** `/tmp/lore-scratch-61bw1` carries the reference `pdp.py` + the D2 re-home in
  `surreal_schema.py` (uncommitted, disposable by `scratch_copy.sh` design — the builder does the real
  re-home). Throwaway probe `/tmp/derisk_typerecord_61b.py` likewise. Remove at will.
- `type::record('principal'/'agent', …)` table names are hardcoded in the emitter (a mild drift vs
  `surreal_schema.PRINCIPAL_TABLE`/`AGENT_TABLE`, NOT cross-checked) — the builder may want a pin.
- Next: the lead runs the contract-adversary + a security-auditor frontier on the settled contract.
