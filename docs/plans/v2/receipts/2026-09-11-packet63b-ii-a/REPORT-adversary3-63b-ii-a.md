# REPORT — adversary3-63b-ii-a (FOCUSED contract-adversary on the MP-5/MP-6 delta, packet 63b wave ii-a)

`brief-base v14 read`
`contract-adversary role read`
`brief project v7 read`
store-ref read (`docs/reference/surrealdb-31-capabilities.md`): §1.1 (FIELD OVERWRITE / INDEX IF NOT EXISTS) · §1.4 (option<> on a POPULATED table, NO ASSERT/DEFAULT) · §1.7 (SCHEMAFULL rejects undeclared top-level keys — why the §4.F message DDL is load-bearing) · §2 (CONTENT / bound `RecordID` links / explicit projection reads NONE as `None`) · §4 (record<> links / ENFORCED `to` edge). Cited, not re-transcribed.

## SUMMARY BLOCK (brief-base §1)

- **VERDICT: CONTRACT INSUFFICIENT — by exactly ONE missing pin (D-NULLTOKEN).** The TWO NEW pins themselves (MP-5, MP-6) are SOUND: satisfiable on a correct build (no C-DEF) and each REDS its named wrong build with controls. The single gap is a **§3.1-mandated leg of `governed.resolve_principal` that no test pins** — surfaced by MP-6's absence-mode quantifier, flagged by the reviser as D-NULLTOKEN, and empirically confirmed here: a plausible wrong build passes the whole file yet crashes in the realistic production absence shape. **This is a lead-decidable completeness call (recommendation + evidence below); I judge it IN-SCOPE, hence the verdict.**
- **P1 headline — did any wrong build survive?** For the DELTA: NO for the pins as written (both MP-5 and MP-6 kill their named wrong builds). BUT a wrong build of the resolve_principal seam the delta relies on (`access_token.subject` direct, no getattr) **passes the full 21-test file** while violating ruling §3.1 (token-absent → None) — the D-NULLTOKEN gap.
- **Satisfiability receipt:** whole-feature reference (ruling §2.3/§3.1/§3.2/§4/§6: `governed.resolve_principal`+`resolve_write_scope`, `local._resolve_write_scope` route, §4.F message DDL, `messages.send`/`_send_fragment` stamp-threading, `server` capability seam + `_comms_register` α/keep/gate + `_comms_send` identity + α render) in a provenance-asserted scratch (`loremaster.__file__ = /tmp/…/scratchpad/ref/loremaster/loremaster/__init__.py`, verified via `scratch_copy.sh --verify-only`) → **`21 passed / 0 failed`** on `test_comms_send_scope_63b_ii_a.py` INCLUDING MP-5 + MP-6, with **NO contract-line patched**. Harder leg: ruff clean (2 auto-fixed import sorts) + mypy clean (4 trivial Optional/`Any|None` narrows in the PRODUCTION reference) → **`21 passed`** still holds.
- **MP-5 discriminates:** door = `_comms_send` OMITTING the §2.3 `_bare(agent_row.id) == subject.agent_id` check → the sibling-capability send **`DID NOT RAISE GovernedDenied`** (RED). Control: MP-5 GREEN on the correct reference.
- **MP-6 discriminates (all three legs):** door = the Reading-A HYBRID `resolve_principal(...) or resolve_operator_principal(...)` on the tokenless branch → contract REDS at leg 1 (`owner_principal` fabricated == carol); probe confirms leg 2 (a `session:s_tok` keep IS minted) + leg 3 (render is a keeper line, not the α bound). Control: MP-6 GREEN on the correct α reference.
- **QUANTIFIER TABLE (P1b):** below — MP-6's invariant is ∀-over-absence-modes `{empty-subject, None-token}` but the contract pins ONLY the empty-subject mode → the None-token door is unguarded (= D-NULLTOKEN). MP-5's invariant is ∀ (agent≡subject) and pinned.
- **REACH TABLE (P1c):** below — MP-6's deny-verb set is DERIVED from `_COMMS_ACTIONS` (not a hand-list); MP-5's mismatch battery reach is a NAMED bound (63b-iii), the equality check itself built + pinned in ii-a. Both safe.
- **MISSING PIN:** **D-NULLTOKEN** — a unit pin `await governed.resolve_principal(None, principal_store=<stub>) is None` (must NOT raise). Defect it catches: a `resolve_principal` doing `access_token.subject` (no getattr) — the natural non-defensive spelling — which crashes `AttributeError` on the token-absent shape `get_access_token()` returns for an unauthenticated call, and which passes the ENTIRE current contract because the `cred` harness structurally cannot produce a None token.
- **Packages considered:** none — no NEW mechanism specified (MP-5/MP-6 are tests; the reference implements the ruled design against this repo's own stores).
- **Reuse ledger:** none — an adversary reference/door-builds ship no reusable production symbol; the reference reconstructs adversary2's recipe and reuses the landed 63a substrate (`get_or_create_keyed`, `stamp_owner`, `_verify_capability_owner`, `resolve_visible_keeps`, `_governed_field_specs`/`_governed_index_statements`) UNTOUCHED.
- **Graded:** `9138687` · HEAD-at-report: `9138687` · SAME (`git rev-parse HEAD`; `9138687` is HEAD). The two new pins live in `test_comms_send_scope_63b_ii_a.py` (delta `607907f..9138687`, +145 lines).
- **decisions-needed:** **D-NULLTOKEN** — my recommendation is PIN IT (a ~4-line unit pin, §3.1-mandated, #131-class, trivially closable); the lead's alternative is a waive-with-bound if token-absent is judged unreachable in ii-a's served world (post-65 every call carries the api-key — see §D-NULLTOKEN). Either closes the verdict; I did not unilaterally waive it because §3.1 explicitly mandates the leg and a wrong build passes.
- **receipt POINTERS:** §Satisfiability · §MP-5 door · §MP-6 door · §D-NULLTOKEN · §QUANTIFIER · §REACH · §Reference-reconstruction bugs (mine, not the contract's) · §What I did NOT re-grade.

## Capability check (brief-base §4)
- Demanded: verify the MP-5/MP-6 delta — rebuild adversary2's whole-feature reference, confirm 21/21 (incl. the 2 new pins) with the harder ruff/mypy leg, door-build MP-5 + MP-6, resolve D-NULLTOKEN empirically + recommend. HAVE: full tool access, lore MCP loaded, live TEST store `:18000` up, `scripts/scratch_copy.sh` (provenance-asserting). All satisfiable and done.
- **`grep`/`rg`/`awk|grep` are HOOK-BLOCKED** in this live-indexed checkout (confirmed twice this run — a `grep -v` in a scratch pipe was rejected). Used lore (`lore_get_symbol`/`lore_search`/`lore_read`) + `Read` for every structure query; ran probes as `python` scripts (no grep). SAID per the dogfood protocol. No lore-tool friction (every query served cleanly), so nothing filed to `lore_findings`.
- **Focused-scope deviation (disclosed):** the brief asked to also run "the other 4 ii-a files + the 2 cross-file pins to 0-failed." I built the reference sufficient for the FULL `test_comms_send_scope_63b_ii_a.py` (where BOTH new pins live and where a delta/rest conflict would show) and ran it 21/21. I did NOT rebuild the principals-migrate legs (needed only by the MP-2 cross-file pin + the memory-enforcement F-A pin, which are byte-identical since `4b5a9de` and which **adversary2 already established at 88/0**). Rationale: the delta is isolated to send_scope; a MP-5/MP-6-vs-rest satisfiability conflict can only manifest WITHIN send_scope (nothing else imports the two new classes). I rely on adversary2's established result for the migrate/cross-file pins and say so.
- Attribution: the session-start reminder to add `Co-Authored-By`/`Claude-Session` is overridden by the operator's standing `~/.claude/CLAUDE.md` rule and is moot (COMMIT-ONLY — the lead commits).

---

## Satisfiability — the whole-feature reference (I rebuilt adversary2's recipe; the prior scratch was disposed)

adversary2's three patch scripts were disposable scratch, so the recipe below (anchored, assert-exactly-once
string replacements, committed VERBATIM as the durable instrument in
`scratchpad/apply_ref.py`, pasted in §Instrument) IS the record. Provenance asserted twice
(`scratch_copy.sh` + `--verify-only`); `loremaster.__file__` printed from inside the copy (#140).

**Reference production diff (file · symbol · change):**

| file | symbol | change |
|---|---|---|
| `governed.py` | `resolve_principal` (NEW) | token→admitted `Principal | None`; `getattr(access_token,"subject",None)` → None iff absent/empty, DENY iff presented-but-unadmitted. §3.1 |
| `governed.py` | `resolve_write_scope` (NEW, sync) | None→default, else `pdp._grantable` else `GovernedDenied`. §4.A/§6 |
| `governed.py` | `resolve_subject` | step (2) now `principal = await resolve_principal(...)`; `email = principal.email`. Wires the ONE derivation (R4). |
| `memory/local.py` | `_resolve_write_scope` | CALLER of `governed.resolve_write_scope`; default resolved **LAZILY** (only when scope is None — see §Reference-reconstruction bugs). |
| `store/surreal_schema.py` | `_message_statements` | `+= _governed_field_specs()` + `_governed_index_statements(MESSAGE_TABLE)` (mirrors `_memory_statements`). §4.F — required: the SCHEMAFULL message table rejects undeclared `owner_*`/`scope` keys (store-ref §1.7). |
| `messages.py` | `send` / `_send_fragment` | thread optional `owner_principal`/`owner_agent`/`scope` into the CREATE CONTENT (owners bound `RecordID` links, store-ref §2). |
| `server.py` | `CommsActionSpec.requires_capability` (NEW field) + `_COMMS_ACTIONS[SEND]` | typed applicability; send spec `requires_capability=True` + `"capability"` in params. §4/§4.D |
| `server.py` | `comms(...)` | `capability: str \| None = None` param + values-dict entry + threaded to the handler dispatch (the FastMCP wrapper left unpatched — R-WIRE, out of ii-a scope; the tests call `AppContext.comms` directly). |
| `server.py` | `_comms_send` | unconditional `_resolve_subject(capability)`, the §2.3 `agent≡subject` check, keep-by-key + "register first" deny, explicit-scope `resolve_write_scope`, the three stamps threaded to `MessageLedger.send`. §2.3/§4.A/§6 |
| `server.py` | `_comms_register` | resolve principal (§3.1); α branch (ownerless, no keep); `get_or_create_keyed` session keep + SF-63-1 foreign gate via `resolve_visible_keeps`; `owner_principal_id` stamp; `ownerless=` to the render. |
| `server.py` | `_render_comms_register` | `ownerless` param → the α bound line (names ownerless · the DERIVED `requires_capability=True` deny-verbs · the two remedies). |

**Receipts (all in the provenance-asserted scratch, live `:18000`, run ALONE with `-p no:xdist`):**
- `loremaster.__file__ = /tmp/…/scratchpad/ref/loremaster/loremaster/__init__.py` (inside the copy — #140).
- **`21 passed in 40.07s`** on `test_comms_send_scope_63b_ii_a.py` with NO contract-line patched (the whole file: R1–R8, the lift layer, R4, **MP-5, MP-6**).
- **Harder leg:** `uv run ruff check` on the 5 changed files → 2 `I001` (auto-fixed) → *All checks passed*; `uv run mypy` on `governed.py`+`server.py` → 4 trivial narrows applied (`email = principal.email`; `keep_store`/`send_keep_store` Optional asserts) → *Success: no issues found*; re-run → **`21 passed`**. No cleanup a correct build demands touches a contract line.
- **No C-DEF:** MP-5 and MP-6 both PASS on the correct reference (contrast the predecessor's MP-1 C-DEF, closed by adversary2).

---

## MP-5 door-build (P1) — `test_a_send_with_a_siblings_capability_denies_and_writes_nothing`

**Wrong build (ruling §2.3 / F4 kernel "no argument moves the stamp"):** a `_comms_send` that OMITS
`_bare(agent_row.id) == subject.agent_id`. `stamp_owner` verifies `alice_w2` (its `(principal, agent)`
binding to alice's token HOLDS), nothing denies, the send proceeds with `sender=alice_w1`,
`owner_agent=alice_w2` and WRITES a row.

- **Reproduced RED** (mismatch send `agent=alice_w1 capability=<alice_w2's>`):
  `E   Failed: DID NOT RAISE <class 'loremaster.governed.GovernedDenied'>` (`:791`). `1 failed in 3.67s`.
  (The `after == before == 0` leg would also have redded — a row was written — but `pytest.raises` fails first.)
- **Positive control:** the correct reference passes MP-5 (green in the 21/21) — the SAME send with
  `alice_w1`'s OWN capability writes exactly one row, and the mismatch DENIES naming `agent="alice_w1"`.
- **Verdict:** MP-5 DISCRIMINATES its named wrong build. Not a C-DEF (passes the correct build).

## MP-6 door-build (P1) — `test_a_tokenless_register_succeeds_ownerless_mints_no_keep_and_names_the_bound`

**Wrong build (ruling §3.2 α — the Reading-A HYBRID):** `principal = await resolve_principal(...) or
await resolve_operator_principal(principal_store)` on the tokenless branch (a self-contained
`resolve_operator_principal` returning the fleet's single admin, carol). It FABRICATES carol as keeper
AND owner for every tokenless register.

- **Reproduced RED** (contract, reds at leg 1): `AssertionError: a tokenless register FABRICATED an owner …
  got owner_principal=RecordID(table_name=principal, record_id='arrz0mvzcnwc9jkhorng'),
  carol='arrz0mvzcnwc9jkhorng'` (`:862`) — the fabricated owner **== carol's pid** exactly.
- **All three legs confirmed violated** (probe `scratchpad/probe_mp6_door.py`, run against the door — the
  contract test stops at leg 1, so I observed 2+3 directly): `LEG1 leg1_RED(fabricated non-None==carol): True` ·
  `LEG2 session:s_tok keep = keep:01M28…  leg2_RED(a keep is minted): True` ·
  `LEG3 render has ownerless-bound = False  leg3_RED(keeper line, NOT the α bound): True`.
- **Positive control:** the correct α reference passes MP-6 (green in the 21/21) — owner NONE, no keep,
  the α bound line naming `send` + `credential` + `migrate-governed`.
- **Verdict:** MP-6 DISCRIMINATES its named wrong build on all three legs. Not a C-DEF.

---

## D-NULLTOKEN (lead-assigned) — RESOLVED empirically; a REAL unpinned in-scope gap

**The question (ruling §3.1):** `resolve_principal` returns None for BOTH "token absent" AND "no subject
presented." MP-6 drives ONLY the empty-subject mode (`holder["email"]=None` → `access_token(subject="")`);
the `get_access_token()`→`None` absence mode is unpinned.

**(a) Does the reference handle both modes?** YES — the reference uses the defensive
`getattr(access_token, "subject", None)` lifted from `resolve_subject`. Probe (`scratchpad/probe_nulltoken.py`,
against the reference):
```
MODE A (empty-subject token)  -> resolve_principal = None
MODE B (None token)           -> resolve_principal = None
```
Both absence modes → None (the α branch). No crash. The principal_store is never consulted (short-circuit),
proving the None-decision is at the seam, not downstream.

**(b) Would a build that handles empty-subject but CRASHES on a None token PASS the current contract?** YES —
this is the gap. Door = `resolve_principal` doing `email = access_token.subject` (the natural NON-defensive
spelling, a plausible builder cleanup of the getattr). Probe against that door:
```
MODE A (empty-subject token)  -> resolve_principal = None                 (empty-subject still works)
MODE B (None token)           -> RAISED AttributeError :: 'NoneType' object has no attribute 'subject'
```
And the SAME door **`21 passed in 41.70s`** on the full `test_comms_send_scope_63b_ii_a.py`. The contract cannot
see the crash because the `cred` harness's `_patched_get_access_token` ALWAYS returns `access_token(subject=…)`
— it wraps `holder["email"]=None` into `subject=""`, and there is no path in any of the 5 ii-a files that makes
`get_access_token()` return `None`.

**Why this is the #131 pattern, not a nicety:** the fixture STRUCTURALLY guarantees the one condition
(`subject=""`, never `None`) under which the None-crashing build is invisible — the exact "THE TEST
ENVIRONMENT IS A FICTION" class this repo has a 100%-production-outage law about. And `None` is the REALISTIC
production absence shape: an unauthenticated / no-ambient-token call yields `get_access_token() → None` (which
is precisely why the shipped `resolve_subject` already reads it with a defensive `getattr`), whereas
`subject=""` is the harness's synthetic stand-in.

**Reachability nuance (the mitigant, stated honestly):** per design F1/I5, post-65 every SERVED call carries the
pkt-49 api-key, so `get_access_token()` returns a real token on the served path; a true None-token arises only
on a broken cutover or a genuinely unauthenticated call. So the SEVERITY is defense-in-depth, not a normal-path
break. But the SPEC (ruling §3.1) explicitly mandates the leg, and a wrong build violating it passes — which is
a missing pin regardless of production reachability.

**RECOMMENDATION (lead decides — Thing #3 is explicitly your call):**
- **PIN IT (recommended).** A ~4-line pure UNIT pin on the seam, no harness monkeypatch needed:
  `assert await governed.resolve_principal(None, principal_store=<stub>) is None` (and asserts it does NOT
  raise), pinning §3.1's token-absent leg directly. Cheap, spec-mandated, kills the `.subject`-direct wrong
  build. (An MP-6 variant with `get_access_token`→None via a local monkeypatch also works but is heavier.)
- **ALTERNATIVE (waive-with-bound).** If you judge token-absent unreachable in ii-a's served world, adjudicate
  it a KNOWN BOUND with the re-open trigger "the first served path that can reach `get_access_token() → None`
  (a hosted / unauthenticated deployment)" and route the None-guard to the builder + cold audit. This is the
  weaker option here because the hole is trivially closable, but it is legitimate and yours to choose.

---

## QUANTIFIER TABLE (P1b) — the delta's invariants

| invariant (new pin) | ∀-over-inputs or guarded? | receipt |
|---|---|---|
| MP-5: a send's `owner_agent` is the SUBJECT's agent (from the capability), never the `agent=` argument | ∀ (agent≡subject check, §2.3) | WB (omit-check door) → `DID NOT RAISE`; control green |
| MP-6: a tokenless register is ownerless + mints no keep + names the α bound | **∀ over absence modes `{empty-subject, None-token}`, but PINNED only on empty-subject** | empty-subject leg: hybrid door REDs all 3 legs (green control). **None-token leg: UNGUARDED → D-NULLTOKEN** (the `.subject`-direct door walks the same "must resolve to None/ownerless" outcome through the unpinned absence door and passes the file) |
| MP-6 render names the DERIVED deny-verb set | ∀ over `requires_capability=True` verbs (derived from `_COMMS_ACTIONS`, not hand-listed) | green on reference; the α render derives `{send}` from the module spec table |

The MP-6 row is the P1b finding: the invariant is a universal over identity-absence, and the contract guards
only the failure mode the harness can express — the classic "guarded-by-known-failure-mode" hole. D-NULLTOKEN
IS that hole, named.

## REACH TABLE (P1c) — the delta's instruments

| instrument (introduced by the delta) | reach DERIVED? | coverage a checked variable? | effect vs proxy? | one-source by mutation? | leg | verdict |
|---|---|---|---|---|---|---|
| MP-6 deny-verb render check (`{v for v,s in _COMMS_ACTIONS.items() if getattr(s,"requires_capability",False)}`) | YES — from `_COMMS_ACTIONS`, not a hand-list | n/a (single render line; the set is derived so a new True-verb joins automatically) | EFFECT (asserts each derived verb literal IS in the rendered α line) | n/a | EMPIRICAL (green on reference; hybrid door reds it) | SAFE |
| MP-5 agent≡capability MISMATCH check | reach = ONE mismatch case in ii-a; the ≥2×≥2 battery is a NAMED bound → 63b-iii (§9 B2) — not a hidden constant | n/a (the EQUALITY CHECK itself is built + pinned in ii-a; the matrix widening is 63b-iii's, declared) | EFFECT (drives a real sibling-capability send; observes deny + zero rows) | n/a | EMPIRICAL (omit-check door reds) | SAFE (bound is named, not hidden) |

Both delta instruments are reach-honest. (The whole-feature REACH table — DDL emitter, F5 population growth,
deny-by-default site coverage, live-classify, the resolve_principal/resolve_operator_principal/resolve_write_scope
lifts — was built and passed by adversary2 at `4b5a9de`; the delta touches none of those instruments, so I build
ON adversary2's table rather than re-deriving it.)

---

## Reference-reconstruction bugs (MINE, not the contract's — disclosed for honesty)

My FIRST reference build failed 2 of 21; both were defects in MY reconstruction, fixed, and are NOT contract
defects (the fixes are pure reconstruction correctness, changing no tested behavior):
1. **Eager default scope** — I resolved `_default_project_scope()` unconditionally in `local._resolve_write_scope`;
   that reads the `keep` table, which the bare `build_memory_backend` fixture never creates
   (`CAUSE: NotFoundError :: The table 'keep' does not exist`). adversary2's recipe resolves the default LAZILY
   (only when scope is None). Fixed → the remember-mutation pin passes.
2. **`render_line` SafeLine guard** — I passed a raw `str` (`", ".join(deny_verbs)`) for the `{verbs}` slot;
   `render_line` requires `SafeLine|Rendered|int`. Wrapped with `sanitise_line`. Fixed → MP-6 render passes.

Both are the kind of thing that only shows by RUNNING the reference — which is why the satisfiability leg is a
build+run, never a read. After both fixes: 21/21, ruff+mypy clean.

## What I did NOT re-grade (built ON adversary2, per the FOCUSED brief)
adversary2 established the contract SUFFICIENT at `4b5a9de` (whole-feature reference 88/0; every R1–R8 rider
discriminates; MP-1..4 closed; the DDL/population/site/live-classify instruments intact). The ONLY change since
is `9138687` (MP-5 + MP-6). I verified the DELTA did not break satisfiability (21/21 on one reference incl. both
new pins) and that both new pins discriminate. I did NOT re-run the migrate legs / the 2 cross-file pins / the
other 4 ii-a files (byte-identical since `4b5a9de`); I rely on adversary2's result for those and say so. My
single finding (D-NULLTOKEN) is one adversary2's pass did not surface — adversary2's own reference used the
defensive getattr, so it never tried the None-crashing wrong build; the reviser's D-NULLTOKEN flag + this
door-build is what caught it.

## Instrument — `scratchpad/apply_ref.py` (the reference recipe, disposable scratch → pasted here as the durable record)
The reference is 20 anchored assert-exactly-once patches across `governed.py` (2), `memory/local.py` (1),
`store/surreal_schema.py` (1), `messages.py` (5), `server.py` (11). The per-file diff table in §Satisfiability
above is the human-readable form; the exact anchors live in the committed-to-scratch `apply_ref.py`. The two
door-builds are single-edit deltas ON the reference: MP-5 = delete the `if _bare_id(agent_row.id) !=
subject.agent_id: raise …` block in `_comms_send`; MP-6 = replace `_comms_register`'s `principal =
resolve_principal(...)` with the `… or resolve_operator_principal(...)` hybrid; D-NULLTOKEN door = replace
`resolve_principal`'s `getattr(access_token,"subject",None)` with `access_token.subject`.

## Method / discipline receipts
- Store law read FIRST (brief step 3): §1.1/§1.4/§1.7/§2/§4 cited, not re-transcribed. The §4.F message DDL is
  load-bearing precisely because store-ref §1.7 (SCHEMAFULL rejects undeclared top-level keys) means the message
  row cannot carry `owner_*`/`scope` without the governed columns landing.
- lore-first for structure: `lore_get_symbol`/`lore_search`/`lore_read` for every production seam
  (`resolve_subject`, `_resolve_subject`, `stamp_owner`, `_verify_capability_owner`, `AgentRegistry.register`,
  `KeepStore.{get_or_create_keyed,get_by_key,add_household_member}`, `resolve_visible_keeps`, `pdp._grantable`,
  `pdp.keep_scope`, `LocalMemoryBackend._resolve_write_scope`, `_message_statements`/`_memory_statements`/
  `_governed_field_specs`/`_governed_index_statements`, `MessageLedger.send`/`_send_fragment`, `comms`/
  `_comms_register`/`_comms_send`/`_render_comms_register`, `CommsActionSpec`/`_COMMS_ACTIONS`, `Principal`/`Keep`
  models). grep hook-blocked → `Read` + `python` probes, SAID. No lore friction filed.
- Provenance asserted (#140): `scratch_copy.sh` + `--verify-only` + `loremaster.__file__` printed from inside the
  copy. Every door-build ran in the same provenance-asserted scratch; the reference restored from a `cp -a`
  content backup (`scratchpad/ref_backup`) between door-builds.
- Controls (P0): every wrong-build RED paired with the correct-reference GREEN (MP-5's own-capability control,
  MP-6's credentialed-register control, the D-NULLTOKEN reference-handles-both control) + the MP-6 three-leg probe.
- COMMIT-ONLY honoured: the ONLY MAIN-tree write is this report; all builds/doors in SCRATCH; git untouched.

**VERDICT: CONTRACT INSUFFICIENT** — the two new pins (MP-5, MP-6) are sound (satisfiable, no C-DEF, each
discriminates its named wrong build), but ruling §3.1's token-absent leg of `governed.resolve_principal` is a
real unpinned gap I judge IN-SCOPE (the D-NULLTOKEN missing pin): a plausible `.subject`-direct wrong build
crashes on the realistic production absence shape yet passes the whole 21-test file, because the harness
structurally cannot produce a None token. Fix is a ~4-line unit pin (recommended); the lead may instead
waive-with-bound. Nothing else in the delta is defective.
