# REPORT — adversary-61b-w1 (CONTRACT ADVERSARY + SECURITY frontier, the PDP CORE)

brief-base v14 read · brief project v7 read

---

## ⭐⭐ RE-GRADE 2 (2026-08-23, delta at 123 pins — #416 + SEC LOWs) — VERDICT: **CONTRACT SUFFICIENT**

The author landed the security-auditor's **#416** (composition-safety cross-principal leak) + **SEC
F2/F3/F4/R4** (LOW). Contract is now **123 pins** (102 pure + 21 live-oracle). I focused-re-graded the
delta against a **rebuilt stdlib-only reference** (PRINCIPAL_TABLE/AGENT_TABLE homed in lorerunes +
used by the emitter; `str|None` owners with empty-string rejected; non-empty identity; `_MUTATING`
DERIVED from Action). **Graded at `599354a` (working-tree; HEAD SAME). Satisfiability: 123/123** in
3.60s, provenance clean, all three re-homes identity-True.

| Finding | Fix landed | My verification (mutation-proven) |
|---|---|---|
| **#416** (latent cross-principal LEAK the entry-point oracle can't see) | every node's `to_surql` is SELF-CONTAINED (parenthesised); a live-store composition pin `And(OwnerPrincipalEq($p), ScopeInKeeps)` returns only owner=$p's rows + a leaky-twin positive control; structural `_has_unparenthesised_top_level_or` pins | ✅ **M7 reproduced:** unparenthesised ScopeInKeeps → the composition pin **REDS leaking `{r12}`** (bob's keep:k9) **while the entry-point equivalence oracle STAYS GREEN** — the pin catches a leak the oracle cannot. Structural pins also RED; positive control non-vacuous. Parenthesised ScopeInKeeps still **IndexScans** (2-keep plan pin green, no #413 regression). ⚠ **Q2 reach (LOW residual, see below).** |
| **SEC-F2** (option<> / NONE owner) | oracle fixture gains r13 (NONE server) + r14 (NONE agent-private); `to_surql` (store NULL) and `matches` (Python None) must agree | ✅ a build where `matches` treats a NONE owner as matching-all → the NONE-agreement pin **REDS** (Python matches r14, store excludes it). |
| **SEC-F3** (empty identity forgery) | Subject rejects empty principal_id/agent_id; Resource rejects empty owner (None still allowed) | ✅ a build dropping the non-empty check → `test_subject_rejects_empty_identity` **REDS** (both fields). |
| **SEC-F4** (`_MUTATING` a hand-list) | `_MUTATING`/audit domain DERIVED = every non-READ Action; `test_every_non_read_action_is_treated_as_mutating` iterates `pdp.Action` | ✅ a hand-list `_MUTATING` omitting SET_SCOPE → the derived pin **REDS** (admin cross-owner SET_SCOPE not audited — M8). |
| **SEC-R4** (PRINCIPAL_TABLE/AGENT_TABLE 2nd copy) | homed in lorerunes, `surreal_schema` IMPORTS them (AST import-not-assign, M9) | ✅ a private `PRINCIPAL_TABLE="principal"` in surreal_schema → `test_governed_table_names_are_imported_from_lorerunes[PRINCIPAL_TABLE]` **REDS**, `[AGENT_TABLE]` stays green. |

**Re-confirmed on the 123-pin suite:** oracle still load-bearing (W1 split-brain: 102 pure GREEN,
oracle RED); charter still green; boundaries still clean (no 62/63/64 reach; the new pins import only
stdlib + `surreal_schema`/`_txn`).

**⚠ Q2 REACH RESIDUAL (LOW — NOT blocking, surfaced per the lead's explicit question and scope law):**
the #416 STRUCTURAL pin `test_no_node_emits_an_unparenthesised_top_level_or` covers
`_one_of_each_node` (DERIVED, single instance each) **PLUS a hand-list** `multi_disjunct =
[ScopeInKeeps(2 keeps), Or(2 children)]`. I proved the multi-disjunct coverage rests on that
**hand-list, not the derivation**: dropping `multi_disjunct` in a scratch copy of the test makes the
pin **PASS the unparenthesised-ScopeInKeeps bug** (its `_one_of_each_node` instance has 1 keep → a
single disjunct → no OR to catch). So a FUTURE multi-disjunct node that emits a top-level OR only at
≥2 args, and is not added to `multi_disjunct`, would slip the structural pin — and the live-store
composition pin is ScopeInKeeps-specific, so it wouldn't catch it either. **Mitigated** (not a present
hole): the closed-algebra gate forces a new node to be ruled in deliberately, the current 8-node
algebra is fully covered, and 63/64 (which actually compose nodes under Ands) re-audit. **Suggested
refinement (optional):** coverage-check the `multi_disjunct` list — derive "every node constructible
with ≥2 disjuncts is exercised at ≥2" — or assert `multi_disjunct` covers each multi-arg-capable node,
so a new one reds until added. This is a nice-to-have hardening of a guard, not a defect in the build.

**VERDICT: CONTRACT SUFFICIENT — release the builder.** Provenance: 123/123 in 3.60s;
`lorerunes.__file__ = /tmp/lore-adv-61bw1/…`; `surreal_schema.PRINCIPAL_TABLE==lorerunes.PRINCIPAL_TABLE`
and `AGENT_TABLE` and `_PRINCIPAL_ROLES is` all True.

---

## ⭐ RE-GRADE (2026-08-23, delta at 106 pins) — VERDICT: **CONTRACT SUFFICIENT**

The author landed all three findings (F3 ruled **stdlib-dataclass**, not pydantic, by the sidecar).
Contract is now **106 pins** (was 102). I focused-re-graded the delta against a rebuilt independent
**stdlib-only** reference (frozen+slots dataclass; charter-clean) on the live 3.2.4 store.
**Graded at `599354a` (working-tree contract files; HEAD SAME). Satisfiability: 106/106.**

| Finding | Fix landed | My verification (mutation-proven) |
|---|---|---|
| **F1** (#413 plan pin inert at 1 keep) | `_two_keep_member{k1,k9}` added to `_all_subjects` + new pin `test_member_read_emitter_with_TWO_keeps_indexscans_no_tablescan` | ✅ literal-IN emitter now **REDS** the 2-keep plan pin (was inert at 1 keep). Drop-a-keep emitter now **REDS** the equivalence oracle at 2 keeps (`only-python=[r11,r12]`) — the multi-keep expansion is now differentially store-tested for BOTH correctness (equivalence) and plan (IndexScan). |
| **F2** (admin SET_SCOPE under-audit un-pinned) | `test_admin_set_scope_into_a_non_grantable_keep_is_audited` (True) + `..._grantable_keep_is_NOT_audited` (False, discriminator) | ✅ **WA4 now REDS** (was 102/102 passing). **Sharing mutation-proven:** one change to the shared `_grantable`/member-SET_SCOPE rule moves BOTH the member-SET_SCOPE-refuse pin AND the admin-audit pin — requires_audit shares the member predicate (routing-not-sharing is caught). |
| **F3** (lorerunes stdlib-only unpinned) | `TestLorerunesStdlibOnlyCharter`: every top-level import ∈ `sys.stdlib_module_names ∪ {lorerunes}`, `deps==[]` backstop; value objects → stdlib `@dataclass(frozen=True, slots=True)` | ✅ charter is **property-DERIVED** (stdlib set from the interpreter, module set from the package glob → **coverage-checked: a NEW module is scanned, not exempt**, proven), vacuity-guarded. Mutation: `import pydantic` → RED; `import loremaster` (sibling) → RED; both-in-a-new-module → RED listing both. A mutable (non-frozen) Subject → `test_subject_is_frozen` RED. |

**Also re-confirmed on the 106-pin suite:** the single-brain oracle is **still load-bearing** (W1
split-brain `OwnerAgentEq.to_surql→"true"`: all 91 pure pins GREEN, oracle REDS). Boundaries still
clean (no 62/63/64 over-reach; the charter pin imports only stdlib — `sys`/`ast`/`tomllib`/`pathlib`).
RED honesty: F2 behavioural pins RED at HEAD via the `_pdp()` gate; the 3 charter pins are invariant
guards (green at HEAD by design — existing lorerunes is already stdlib-only — and mutation-proven).

**One residual (minor, NOT blocking):** the value-object pins assert BEHAVIOUR (frozen +
dataclass-rejects-unknown-kwarg), which hold with or without `slots=True` — so `slots` is documented
but not independently enforced (a non-slots frozen dataclass also passes). The immutability / no-extra
behaviour IS pinned; `slots` is a hygiene choice. No action needed.

**VERDICT: CONTRACT SUFFICIENT — release the builder.** Provenance receipt:
`lorerunes.__file__ = /tmp/lore-adv-61bw1/lorerunes/lorerunes/__init__.py`,
`surreal_schema._PRINCIPAL_ROLES is lorerunes.PRINCIPAL_ROLES == True`, 106/106 in 2.58s.

---

*(The original INSUFFICIENT grade + full probe record below is the historical record that produced
the three fixes above — kept intact, superseded by this re-grade.)*

## SUMMARY BLOCK
- **State:** done. Graded the 102-pin RED contract (86 pure `lorerunes/tests/test_pdp_core.py`
  + 16 live-store oracle `loremaster/tests/test_pdp_oracle_61b.py`) by building an INDEPENDENT
  stdlib-only reference PDP + ~15 wrong builds in scratch, run against the REAL 3.2.4 store.
- **VERDICT: CONTRACT INSUFFICIENT** — 1 wrong build passes all 102 (F2), 1 load-bearing pin
  cannot fail at its fixture (F1). Both are cheap refinements to an otherwise STRONG contract;
  the single-brain oracle, per-action discriminators, coverage/reach pins and D2 sharing guards
  are all genuinely load-bearing (proven below).
- **P1 headline — did a wrong build survive?** YES (F2): `requires_audit` for admin `SET_SCOPE`
  is un-pinned; a routing-not-sharing build (drops grantability in the audit member-check)
  passes **102/102** while UNDER-auditing an admin re-scoping their own row into a keep they
  are not in (a §9 load-bearing bypass). Reproduced (WA4).
- **P1 second — the packet's trust anchor holds:** a split-brain PDP (`to_surql` drops the
  owner_agent conjunct, `matches` unchanged) passes **all 86 pure pins GREEN** and the ORACLE
  **REDS** (W1). The live-store oracle IS load-bearing and IS the real 3.2.4 engine (2.85s wall,
  UnionIndexScan plans observed) — a Python mock could not exhibit this.
- **Deviations:** built the reference **stdlib-only** (frozen dataclasses), NOT pydantic — to
  prove the contract does not FORCE pydantic into the stdlib-only lorerunes member (see F3).
- **Packages considered:** none — no mechanism specified (I graded a contract; the contract's own
  `pycasbin→bespoke` / `pydantic→reuse` survey is verified in F3, not re-derived).
- **Reuse ledger:** none (adversary probes only; instruments pasted verbatim / committable —
  `/tmp/probe_keepcount_61b.py`, `/tmp/probe_contains_61b.py`, pasted in the probe record).
- **Graded:** `599354a` · HEAD-at-report: `599354a` · SAME. (Wave is UNCOMMITTED; the contract
  files are untracked at this sha — graded as-on-disk.)
- **Decisions needed (for lead-61 / operator):**
  1. **F3 (Fork B vs Fork D tension):** may `lorerunes` depend on pydantic, or must the PDP value
     objects be stdlib-only? `pyproject.toml` says `dependencies = []` INTENTIONALLY; `blankness.py`
     explicitly ruled pydantic OUT of lorerunes; Fork D says "pydantic value objects". No pin guards
     either way. My stdlib-only reference proves the contract is satisfiable without pydantic.
- **Receipt pointers:** satisfiability + provenance → §Satisfiability; wrong-build matrix →
  §"P1 wrong-build campaign"; F1 mutation-proof (3 legs) → §F1; F2 (WA4 passes 102) → §F2;
  P1b quantifier table → §P1b; P1c reach table → §P1c; security verdicts → §Security.

---

## What I did (instruments)

1. **Independent reference build (stdlib-only).** Wrote `lorerunes/lorerunes/pdp.py` from the
   design + contract alone (frozen `@dataclass` value objects, an `enum.Enum` Action, a closed
   `Predicate` ABC with `to_surql`/`matches`, per-action builders, `authorize`/`authorize_filter`),
   re-exported it from `__init__.py`, and applied the D2 re-home in `surreal_schema.py` — all in a
   provenance-asserting scratch (`./scripts/scratch_copy.sh /tmp/lore-adv-61bw1`).
2. **Ran the full contract against it** → 102/102 (satisfiability + positive control).
3. **Built ~15 wrong PDPs** by patching the reference in scratch and running the targeted pins on
   the REAL store `ws://127.0.0.1:18000` (never `:18500`). The oracle IS the engine; every negative
   is paired with a positive control.

### Satisfiability receipt (#140 provenance — runs its OWN code)
```
lorerunes  __file__ = /tmp/lore-adv-61bw1/lorerunes/lorerunes/__init__.py
loremaster __file__ = /tmp/lore-adv-61bw1/loremaster/loremaster/__init__.py
re-home identity: surreal_schema._PRINCIPAL_ROLES is lorerunes.PRINCIPAL_ROLES == True

pure-core : 86 passed in 0.10s
oracle    : 16 passed in 2.85s   (live 3.2.4 store; UnionIndexScan plans observed)
TOTAL     : 102 / 102  against an INDEPENDENT stdlib-only reference build
```
The reference is stdlib-only (no pydantic) — so the 102 pins are satisfiable without adding a
third-party dep to lorerunes. **RED honesty (P7):** at HEAD the pure file collects clean and
86 fail via the `pytest.fail` #133 gate (not ImportError); the oracle collects 16 clean and all
fail via the same gate ("the 61b-w1 PDP core is not built yet — lorerunes is missing [...]").

---

## VERDICT: CONTRACT INSUFFICIENT

Two concrete findings meet the bar (one wrong build survives; one load-bearing pin cannot fail),
plus one escalation and residuals. The contract is otherwise strong — I tried hard to break the
single-brain oracle and could not (W1 confirms it catches what the pure pins miss).

---

### F2 — MISSING PIN (a wrong build passes 102/102): `requires_audit` for admin `SET_SCOPE` is un-pinned

**The wrong build that survives (WA4):** `requires_audit` is specified single-brain as
`allowed ∧ admin ∧ mutating ∧ ¬member_predicate(action).matches(resource)`. A build whose
audit-side member-check for `SET_SCOPE` drops the grantability conjunct — a *routing-not-sharing*
private check, e.g. bare `owner=me` instead of the real grantability-gated `SET_SCOPE` predicate —
**passes all 102 pins** and UNDER-audits:

```
admin (keeps=∅) SET_SCOPE own row (alice/ag_a) target=keep:k9 (admin NOT in k9):
   CORRECT build: allowed=True  requires_audit=True   (a member could NOT grant k9 → load-bearing bypass → §9 audit)
   WA4     build: allowed=True  requires_audit=False  ← the admin bypass goes UNAUDITED
WA4 full suite: 102 passed in 2.67s
```

**Why no pin catches it:** `TestRequiresAudit` fixtures cover WRITE cross-owner / WRITE own-row /
member WRITE / SET_OWNER-always / READ-never — but **nothing about `SET_SCOPE`**.
`test_requires_audit_implies_audit`/`_implies_allowed` only checks the *implication* (True⟹allowed),
which a False-when-should-be-True build satisfies vacuously. The oracle does not cover
`requires_audit` (it is a Python-only obligation flag, not emitted to SQL — correct by design).

**The pin that should exist:**
```python
def test_admin_set_scope_into_a_non_grantable_keep_is_audited(self) -> None:
    # admin (keeps=∅) re-scopes its OWN row into keep:k9 (admin ∉ k9): a member could not grant
    # k9 → the admin used a load-bearing bypass → §9 requires the audit.
    pdp = _pdp()
    admin = _admin(pdp)  # alice/ag_a, keeps=∅
    own = _resource(pdp, table=_GOV, owner_principal="alice", owner_agent="ag_a",
                    scope=pdp.SCOPE_PRINCIPAL_PRIVATE)
    d = pdp.authorize(admin, pdp.Action.SET_SCOPE, own, target_scope=pdp.keep_scope("k9"))
    assert d.allowed is True and d.requires_audit is True
```
**And the rider the single-brain design demands but the contract drops:** *mutation-prove that
`requires_audit` SHARES the member predicate* — change the member `SET_SCOPE` grantability rule and
BOTH the `authorize_filter(SET_SCOPE)` pin AND this audit pin must move. Today `requires_audit`'s
sharing is proven ONLY for the SET_OWNER path (WA3, which drops all grantability, is caught by
`test_admin_set_owner_is_always_audited`), leaving the SET_SCOPE grantability path unshared-provable.

**Severity:** MEDIUM. Realistic manifestation is the *over-audit* (safe) direction — the design's own
Fork G formula (`member_predicate(action)`, no `target_scope`) drops the target, which I confirmed
passes 102/102 too (WA2) but only over-audits admin's own grantable re-scope. The *under-audit*
(WA4) is the adversarial worst case and is the one that matters for §9.

---

### F1 — FIXTURE DISCRIMINATION: the #413 read-emitter plan pin cannot fail at its 1-keep fixture

`test_member_read_emitter_indexscans_no_tablescan` is the design's **"single most important
store-law surface"** (store-ref §2 / #413). It runs the emitted member-READ predicate for
`_alice_member`, whose `visible_keep_ids` is a **single** keep `{k1}`. **A 1-element `IN` IndexScans;
the trap needs ≥2 elements** — so a build that regresses `ScopeInKeeps` to a literal `scope IN $keeps`
does NOT TableScan at this fixture, and this pin PASSES on the wrong build. The regression is caught
only by the SYNTACTIC sibling pin `test_the_emitted_read_fragment_contains_no_literal_IN` (a string
check for `" IN "`) — which a non-`IN` TableScanning spelling (e.g. `CONTAINSANY`) evades.

**Mutation-proof (3 legs, `_alice_member` perturbed to 2 keeps in a scratch copy of the test):**
```
LEG A  correct build, 2-keep fixture  → plan pin PASSES  (1 passed)   ← perturbation valid, not a botched expectation
LEG B  literal-IN build, 2-keep       → plan pin REDS    (1 failed)   ← 2 keeps DISCRIMINATE
BASE   literal-IN build, 1-keep (shipped fixture) → plan pin PASSES   ← the pin CANNOT FAIL on the regression it exists to catch
```
Live plan evidence (`/tmp/probe_keepcount_61b.py`, positive-control walker):
```
1 keep {k1}     LITERAL_IN  → TableScan(gov)=False (IndexScan)   ← 1-element IN IndexScans
2 keeps {k1,k9} LITERAL_IN  → TableScan(gov)=True                ← the #413 trap fires at 2
2 keeps {k1,k9} EXPANDED    → TableScan(gov)=False (UnionIndexScan)
```
Corollary gap: **no oracle subject has ≥2 visible keeps** (`_all_subjects` = 4 subjects, all ≤1 keep),
so the multi-disjunct `ScopeInKeeps` expansion (`scope=$k0 OR scope=$k1`) is **never differentially
tested against the real engine** — only the isolated node shape (the pure `TestScopeInKeepsExpansion`
2-keep pin) is.

**The fix (both halves, one change):** add a **≥2-visible-keep subject** to `_all_subjects` and use it
for `test_member_read_emitter_indexscans_no_tablescan`. Then the plan pin discriminates (LEG B) AND
the store-truth equivalence exercises the multi-keep expansion.

**Severity:** MEDIUM. The literal-`IN` regression IS caught by the contract as a whole (pure shape pin
+ syntactic pin), so no wrong build fully waves through *via a literal IN*; but the LOAD-BEARING plan
pin is decoration at the fixture, and the syntactic pin it leans on is defeated by any TableScanning
spelling without a `" IN "` token — leaving the ≥2-keep store behaviour unguarded by the pin credited
with guarding it.

---

### F3 — ESCALATION (Fork B vs Fork D): lorerunes stdlib-only is unpinned where the value-object impl is decided

The contract requires frozen/`extra=forbid`/domain-validated value objects (Fork D) and the author
built them with **pydantic**. But:
- `lorerunes/pyproject.toml`: `dependencies = []` — *"INTENTIONALLY EMPTY, AND IT IS THE WHOLE
  CONSTRAINT … A third-party dependency added here is inherited by every other member, so it is a
  design decision, not a tidying."*
- `lorerunes/lorerunes/blankness.py:12`: *"A `pydantic` `Field(min_length=1)` was ruled out"* —
  pydantic was DELIBERATELY excluded from lorerunes.
- Fork B header: *"lorerunes (stdlib-only)"*.

pydantic imports in the workspace ONLY because a sibling (loremaster) drags it in; a pydantic-based
`pdp.py` + `pydantic` added to lorerunes deps silently breaks the stated law, and **no pin catches it**
(the Fork B "imports no sibling" pin is (a) deferred to 61b-w2 and (b) would not catch a third-party
dep anyway). The value-object implementation is decided in **w1**, so the guard belongs in w1.

This is a genuine two-readings-different-code design inconsistency (Fork B vs Fork D), of exactly the
class the contract author already escalated (D1/D4). **It needs a lead/operator ruling**, not a silent
builder pick. My stdlib-only reference (102/102) proves the contract is satisfiable without pydantic,
so "stdlib-only, hand-rolled frozen dataclasses" is a clean resolution; alternatively rule pydantic a
sanctioned lorerunes dep and update the pyproject comment + blankness.py note. Either way, **pin the
resolution** (a `test_lorerunes_pdp_is_stdlib_only` import scan, or a deliberate deps entry).

---

## P1 wrong-build campaign (the full matrix)

All against the reference at `/tmp/lore-adv-61bw1`; each patch applied to a fresh copy of the
reference `pdp.py`, targeted pins run, reference restored. ✅ = the contract CAUGHT it (RED).

| # | Wrong build | Expected guard | Result |
|---|---|---|---|
| W1 | **split-brain oracle-only**: `OwnerAgentEq.to_surql→"true"`, `matches` unchanged | oracle only | **86 pure PASS, oracle REDS** ✅ (proves the oracle is load-bearing) |
| W2 | IN-regression: `ScopeInKeeps→"scope IN $keeps"` | #413 pins | `no_literal_IN` REDS ✅; **plan pin PASSES ✗ (F1)** |
| W3a | partial-abstract node (matches only) | reach law | `test_no_predicate_subclass_is_partially_abstract` REDS ✅ |
| W3b | new concrete node | closed-set | `closed_algebra` + `every_node_has_working_to_surql` RED ✅ |
| W4a | READ drops owner_principal (cross-principal leak) | isolation | `cross_principal_isolation_on_read` + `read_visible_set` RED ✅ |
| W4b | WRITE principal-private = owner_principal only (reading 2) | reading-1 | `reading_1_a_sibling…cannot_write` + `write_visible_set` RED ✅ |
| W4c | DELETE + household conjunct | owner-any-scope | `member_delete_is_owner_only_across_every_scope` RED ✅ (r11 lost) |
| W4d | SET_SCOPE bare owner=me (drop grantability) | D4(b) | `discriminating_own_row` + `not_in_is_refused` + `filter_norows` RED ✅ |
| W4e | SET_OWNER = owner_me (member allowed) | admin-only | both SET_OWNER pins RED ✅ |
| W5a | drop audit carve-out (admin AllRows always) | Fork G | pure carve-out pins RED ✅; oracle `admin_mutating_audit_selects_zero_rows` RED ✅ |
| W5b | requires_audit audits EVERY admin mutating | discriminator | `admin_own_row_write_is_NOT_audited` RED ✅ |
| W5c | requires_audit never fires | discriminator | `admin_cross_owner_write` + `admin_set_owner_always` RED ✅ |
| W7 | D2 revert (private copies in surreal_schema) | sharing | BOTH sharing pins RED ✅ |
| W7b | D2 half-revert (separate-but-equal `_PRINCIPAL_ROLES` tuple) | sharing | identity pin RED ✅, AST pin correctly GREEN |
| WA2 | requires_audit member-check drops `target_scope` (design-literal) | — | **102 PASS ✗** (over-audit, benign; un-pinned) |
| WA3 | requires_audit = private bare owner_me (all actions) | — | SET_OWNER pin RED ✅ (partial guard) |
| WA4 | requires_audit drops grantability for SET_SCOPE only | — | **102 PASS ✗ (F2)** — under-audits an admin bypass |

---

## P1b — QUANTIFIER TABLE (∀-over-inputs vs guarded-by-failure-mode)

| Invariant | ∀ / guarded | Receipt |
|---|---|---|
| §5 equivalence `authorize == authorize_filter.matches` | **∀** over fixture (pure `_cross_product` + oracle `_all_subjects×Action×rows`) | W1 (a to_surql/matches split passes all pure, reds oracle). ⚠ HOLE: no subject ≥2 keeps → multi-keep expansion never store-tested (F1). |
| `requires_audit ⟹ allowed` | ∀ over `_cross_product` | holds; W5b/W5c red value pins. |
| **`requires_audit` correctness** | **guarded** — WRITE(×2)/SET_OWNER/READ fixtures; **SET_SCOPE MISSING** | **WA4 passes 102/102 (F2).** |
| READ visible-set | guarded (exact 12-row set) | W4a reds. |
| cross-principal isolation | guarded (r5/r6; 2-principal, symmetric) | W4a reds; oracle covers bob-side via equivalence. |
| WRITE reading-1 (exact (p,a)) | guarded (r4 = sibling agent, the ≥2-agent discriminator) | W4b reds. |
| DELETE owner-any-scope | guarded (r11 = left-keep owner) | W4c reds. |
| SET_SCOPE grantability | guarded (own-row k9 vs k1) | W4d reds. |
| SET_OWNER = NoRows (members) | guarded (own row) | W4e reds. |
| admin AllRows + audit carve-out | guarded (per-action × audit table; pure + oracle) | W5a reds both. |
| IR-node interpreter coverage | **∀** over DERIVED concrete-node set | W3a/W3b red. |

---

## P1c — REACH TABLE (per guard/scan the contract introduces or relies on)

| Instrument | reach DERIVED? | coverage a checked var? | effect vs proxy | one-source / mutation-proven | legs run |
|---|---|---|---|---|---|
| `_concrete_nodes` IR-coverage | **DERIVED** (`Predicate.__subclasses__` recursion) | **YES** — closed-set reds on growth (W3b), partial-abstract reds (W3a), non-vacuity guard present | EFFECT (constructs + calls both interpreters) | single home (lorerunes) | empirical (W3a/W3b) |
| D2 `_module_binds_name_by_import_from` (AUDIT_TABLE) | property (AST import-not-assign) | single-name (not a growing set) | EFFECT (parses real source AST) | **MUTATION-PROVEN** (W7/W7b) | empirical |
| D2 `_PRINCIPAL_ROLES` identity | object identity (`is`) | single-name | EFFECT | **MUTATION-PROVEN** (W7/W7b — separate-but-equal tuple reds) | empirical |
| **live-store equivalence oracle** | subject set = **HAND-LIST** (4, all ≤1 keep) ⚠; Action = derived enum | **PARTIAL** — misses ≥2-keep dimension (F1) | EFFECT (real engine) | the W1 single-brain proof | empirical |
| **#413 read-emitter plan pin** | fixture = **1-keep** subject ⚠ | **NON-DISCRIMINATING at 1 keep (F1)** | EFFECT (real EXPLAIN) + positive controls | positive control fires at 2 keeps but DUT runs at 1 (mismatch) | empirical (3-leg proof) |
| **`requires_audit` member-predicate sharing** | — | **NOT mutation-proven for SET_SCOPE grantability (F2)** | — | ROUTING-NOT-SHARING passes (WA4) | empirical (WA2/WA3/WA4) |

Reach caveat (residual, not a finding): `_concrete_nodes` via `__subclasses__()` sees only IMPORTED
modules — a node added in a non-imported module is invisible. Fork B homes all IR nodes in lorerunes
(imported), so this holds today; it is a reach bound worth a one-line note.

---

## SECURITY section (isolation / carve-out / anti-injection / equivalence-as-security)

- **Cross-principal isolation (§9, the paramount property): PASS.** READ isolation pinned (alice ≠
  bob private, r5/r6); a leak build (W4a, drops owner_principal) REDS. Both sides covered: the oracle
  iterates `_all_subjects` incl. `_bob_member`, so a bob-side leak reds the store equivalence. WRITE
  isolation: a sibling-agent write of a principal-private row (reading 1) is refused and pinned (r4);
  W4b reds a reading-2 build. **No isolation hole found.**
- **Admin audit carve-out (§9, the one carve-out from admin-is-full): PASS.** admin canNOT mutate
  audit (pure `TestTheAuditCarveOut` + oracle `admin_mutating_audit_selects_zero_rows`), admin CAN
  still READ audit, a denied audit mutation is not itself audited. Dropping the carve-out (W5a) REDS
  pure AND oracle. The carve-out is a `NoRows` NODE inside the one expression (not a bypass beside it),
  so §5 holds — pinned.
- **Anti-injection (as far as 61 owns it): PASS on the caller-supplied surface.** A hostile
  principal id and all keep values are pinned BOUND, never interpolated; owner_agent (`ag_a`) is also
  checked not-in-fragment. `#415` derive-from-id is correctly a docstring FORWARD-NOTE (63/64), NOT a
  false 61b enforcement claim. **Residual (F4, LOW/benign):** the FIXED scope literals
  (`agent-private`/`principal-private`/`server`) are not pinned bound-not-interpolated — a build
  emitting `scope = 'server'` (literal) passes; harmless because these are module constants, not
  attacker-controlled, but it diverges from store-ref §2's "bind every value."
- **Equivalence-as-security (no writable-but-invisible / visible-but-unwritable-by-a-different-rule):
  STRUCTURALLY SOUND, with a coverage hole.** W1 proves the LIVE oracle catches a `to_surql`/`matches`
  divergence that all 86 pure pins miss — the design's central claim is real and the oracle is the
  engine, not a mock. **But** the equivalence ∀ never exercises ≥2 keeps (F1), so the multi-keep
  read-filter's engine behaviour is unproven.
- **§9 audit-trail completeness: GAP (F2).** admin `SET_SCOPE` `requires_audit` is un-pinned; an
  admin re-scoping their own row into a non-member keep can go unaudited in a routing-not-sharing
  build that passes 102/102.
- **Boundaries: CLEAN.** No pin reaches `get_access_token`/`AccessToken`/credential mint (62); no pin
  writes/migrates comms/memory/task/finding rows (63/64). The oracle imports only `surreal_schema`
  (D2 re-home — 61b scope) and `_txn.execute_transaction` (store-law §3). No over-reach.

---

## Residuals (individual verdicts — nothing swept)

- **`requires_audit` not in the oracle:** CORRECT by design (an in-process obligation flag, not a
  store filter) — not a gap.
- **No member+audit-table pin:** members reach `audit` only via `AuditStore.append` (61a, append-only)
  — out of 61b-w1's PDP scope; verb routing is 63/64. Note only.
- **`Decision` not pinned frozen/`extra=forbid`:** the design calls it a value object; a mutable
  Decision passes. LOW — a one-line pin would match the Subject/Resource idiom.
- **`type::record('principal'/'agent', …)` table names hardcoded in the emitter** (author already
  flagged): a mild drift vs `surreal_schema.PRINCIPAL_TABLE`/`AGENT_TABLE`, un-cross-checked. LOW.
- **`_HOSTILE_ROWS` byte-parity between the two files:** VERIFIED identical (the "same set" claim holds).

---

## Probe record (commands + real output)

### Reference build (stdlib-only) + satisfiability
`scripts/scratch_copy.sh /tmp/lore-adv-61bw1`; wrote `lorerunes/lorerunes/pdp.py` (frozen dataclasses,
closed Predicate ABC, per-action builders), re-export in `__init__.py`, D2 re-home in
`surreal_schema.py`. Provenance + 102/102 as in §Satisfiability. `pdp.py` kept at
`/tmp/lore-adv-61bw1/lorerunes/lorerunes/pdp_ref.py` as the wrong-build baseline.

### W1 — split-brain oracle-only (the trust anchor)
`OwnerAgentEq.to_surql` → `"true", {}` (matches unchanged):
```
pure-core: 86 passed in 0.07s
oracle:    3 failed, 1 passed  (test_authorize_equals_the_emitted_filter_over_the_store REDS)
```
The store selects alice's sibling-agent (r2) agent-private row via `owner_principal=$p AND true`,
Python `authorize` excludes it → mismatch. Only the engine can see this.

### F1 — the 1-keep blindness (3-leg mutation proof)
```
LEG A correct build, _alice_member perturbed to {k1,k9}: plan pin 1 passed
LEG B literal-IN build, {k1,k9}:                          plan pin 1 failed   ← discriminates at 2 keeps
BASE  literal-IN build, shipped {k1}:                     plan pin 1 passed   ← cannot fail at 1 keep
```
`/tmp/probe_keepcount_61b.py` (committable to `scripts/` — pasted logic in this run): EXPLAIN over the
live store shows 1-element IN → IndexScan, ≥2-element IN → TableScan, EXPANDED → UnionIndexScan at all
cardinalities. `/tmp/probe_contains_61b.py`: `$keeps CONTAINSANY [scope]` (no `" IN "` token)
TableScans at 1 keep with correct results — i.e. the syntactic pin's blind spot.

### F2 — WA4 passes 102/102
```
WA4 (requires_audit member-check drops grantability for SET_SCOPE): 102 passed in 2.67s
divergence: admin SET_SCOPE own row → keep:k9  requires_audit  correct=True  WA4=False
```

### Store / discipline
TEST store `ws://127.0.0.1:18000` only (systemd `spike-surreal` active); the oracle is the REAL
3.2.4 engine; every negative paired with a positive control; no repo file edited (all probes in
`/tmp/lore-adv-61bw1` scratch + `/tmp/probe_*.py`). Scratch is disposable (`scratch_copy.sh` design).

---

## Bottom line
**CONTRACT INSUFFICIENT** — fix F2 (add the admin-SET_SCOPE-audit pin + mutation-prove requires_audit
sharing), F1 (a ≥2-keep oracle subject), resolve F3 (operator ruling on pydantic-in-lorerunes). None
is a structural flaw: the single-brain oracle, per-action discriminators, coverage/reach guards and
D2 sharing pins are all load-bearing and mutation-proven. This is a strong contract two small pins and
one ruling away from airtight.
