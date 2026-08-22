## REPORT-adversary-60-w2b — CONTRACT-ADVERSARY re-pass, packet 60 wave 2 (assembled keep CLI + FR-3)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK

- **VERDICT: CONTRACT SUFFICIENT** — no wrong build survives the ASSEMBLED contract; every new pin
  bites independently; the whole thing is satisfiable together.
- **state:** done — full-contract satisfiability + all 4 focused new-pin bites + inter-pin scan +
  3 round-1 spot-checks run empirically in a provenance-asserted scratch reference build.
- **P1 headline:** the complete assembled contract (w2c blocker + R1 + R2; w2d FR-3 store + ∀-verb CLI)
  → **92 passed / 0 failed** on the reference; the round-1 blocker (no-op `_cmd_set_rank`) is now caught
  by **TWO** independent pins (the blocker pin AND w2d's ∀-verb set-rank ghost pin).
- **new-pin bites (wrong build → red pin + control), all independent of the revisers' proofs:**
  set-rank no-op → blocker reds (+ ∀-verb set-rank reds), legal-rank control green;
  FR-3 dropped → ghost store pin reds, asymmetry pin green; raise-on-EVERY-absent-membership →
  asymmetry pin reds, ghost pin green (NO collapse); new `--keep` verb → ∀-verb reach pin reds;
  5th `_KEEP_TYPES` value → R1 coverage pin reds (parse pin still accepts silently — R1's whole point).
- **new gaps found:** none blocking. ONE LOW residual (§Residuals R-A): the dm-reject content check
  `"dm" in lowered` is a loose substring; no plausible builder message exploits it.
- **deviations:** none material. Scratch `/tmp/pkt60w2b-adv` left behind (disposable rsync copy;
  `rm -rf` guardrail-denied — see §Scratch).
- **Packages considered:** none — no mechanism specified (the reference reuses `argparse` + the
  committed wave-1 `KeepStore`; all pins are test-only introspection).
- **Reuse ledger:** none — I introduced NO production symbol; my only instrument is
  `apply_reference.py` (scratch-only, pasted verbatim §Instruments).
- **Graded:** `5b7180c` · HEAD-at-report `5b7180c` · SAME. Graded artifact = the working tree at
  `5b7180c` (`test_keeps_cli.py` UNTRACKED, `test_keeps_store.py`+`principals.py` MODIFIED; `keeps.py`
  committed with the FR-2 Q2b wrap at `e019477`, WITHOUT the FR-3 amend).
- **decisions-needed:** none — proceed to build. (R-A is a LOW tighten-if-cheap, lead's call, not a gate.)
- **receipts:** satisfiability → §Satisfiability; bites → §Bites; inter-pin → §Inter-pin; spot-checks →
  §Spot-checks; quantifier → §P1b; reach → §P1c; residual → §Residuals; instrument → §Instruments.

---

## Scratch provenance (finding #140)

`./scripts/scratch_copy.sh /tmp/pkt60w2b-adv` (provenance-asserting). The copy runs its OWN code:

```
PROVENANCE loremaster.__file__ = /tmp/pkt60w2b-adv/loremaster/loremaster/__init__.py
```

RED-at-stub baseline (before the reference), confirming the designed RED state + no collection errors:
- `tests/test_keeps_store.py` → **1 failed / 44 passed** — only the FR-3 ghost pin
  (`test_remove_household_on_a_GHOST_keep_is_LOUD_KeepNotFoundError`, `DID NOT RAISE`, i.e. today's
  silent no-op — RED for the right reason).
- `tests/test_keeps_cli.py` → **25 failed / 22 passed** (47 items) — every live keep verb hits
  `build_keep_store`'s `NotImplementedError` (`principals.py:882`, OUTSIDE `_dispatch_keep`'s try →
  propagates → behavioural RED, never a laundered exit 1). The R1 coverage pin + the R3 reach pin are
  GREEN offline at stub (structural), as designed. Both new families
  (`TestAdversarySetRankErrorPath`, `TestANonexistentKeepIsLoudForEveryKeepConsumingVerb`) RED at stub.

---

## Satisfiability (do-first, 0-failed against a known-correct reference build)

Reference = 5 CLI surfaces + the FR-3 one-liner (built by `apply_reference.py`, §Instruments; each
replacement asserted exactly-once, "REFERENCE BUILD applied cleanly"):
- `build_keep_store` — lazy `from loremaster.keeps import KeepStore`; mirror `build_principal_store`
  (url / namespace / `effective_surreal_database` / `resolve_config_value(user_env)` /
  `resolve_secret(password_env)`), minus `dim`.
- `_cmd_create_keep` — per-`type` rule (project/team → `raise ValueError("--name is required for --type
  {type}")`; dm-with-name → `raise ValueError("--name is not valid for --type dm …")`) then
  `create_keep(...)` + `print(keep.id)` + `return 0`.
- `_cmd_add_household` / `_cmd_remove_household` / `_cmd_set_rank` — one-line delegations, `return 0`.
- `keeps.py` FR-3 amend — in `remove_household_member`, after the `get_keep` the keeper-lockout guard
  already does: `if keep is None: raise KeepNotFoundError(...)` BEFORE the DELETE.

```
cd /tmp/pkt60w2b-adv/loremaster && uv run pytest -n auto tests/test_keeps_cli.py tests/test_keeps_store.py
  92 passed in 7.38s
```

The COMPLETE assembled contract (47 CLI + 45 store) is satisfiable together, provenance asserted inside
the copy. Re-run as a POSITIVE CONTROL after all bites (files restored byte-exact to the reference):
**92 passed** again — so every mutation below was reversible and the green is real, not a botched restore.

---

## Bites — each new pin catches the exact wrong build it exists for (independent builds, not the revisers' proofs)

### Bite 1 — set-rank blocker (w2c) → **CLOSED, doubly**
WB: `_cmd_set_rank` reverted to the no-op `return 0` (never calls `KeepStore.set_rank`). Full CLI file:
```
FAILED …TestANonexistentKeepIsLoudForEveryKeepConsumingVerb::test_a_nonexistent_keep_is_a_loud_exit_1[set-rank]
FAILED …TestAdversarySetRankErrorPath::test_set_rank_with_an_unruled_rank_is_loud_and_nonzero
2 failed, 45 passed
```
The no-op is caught by BOTH the blocker pin (real keep + `--rank overlord` → store rank ASSERT rejects
→ exit 1) AND w2d's ∀-verb set-rank ghost pin (no-op on a ghost keep returns 0, not exit 1). The
positive control `test_set_rank_with_the_legal_rank_still_succeeds` stays GREEN (adversary class alone:
`1 failed, 1 passed`). Everything else (45) passes on the no-op — so those two pins are exactly what
stands between a no-op set-rank and green. (Round 1 had only the blocker pin; the assembly adds a
second, independent catcher.)

### Bite 2a — FR-3 ghost store pin (w2d) → **CLOSED**
WB: dropped the FR-3 `if keep is None: raise` (reverting to the pre-FR-3 silent-on-ghost no-op).
`TestRemoveHouseholdMember`:
```
FAILED …test_remove_household_on_a_GHOST_keep_is_LOUD_KeepNotFoundError   (DID NOT RAISE)
1 failed, 3 passed
```
The ghost pin reds; the asymmetry pin + the 2 existing pins stay GREEN.

### Bite 2b — the two remove pins do NOT COLLAPSE (the discriminator)
WB: raise `KeepNotFoundError` on EVERY absent membership (a builder "fixing" ghost-loudness by
always-raising). `TestRemoveHouseholdMember`:
```
FAILED …test_remove_a_non_member_from_a_REAL_keep_is_a_benign_no_op
      (KeepNotFoundError: 'dave@example.com' is not a member of keep 'keep:…')
1 failed, 3 passed
```
The ASYMMETRY pin reds (dave = a real non-member of a real keep, raised on) while the ghost pin PASSES
(it raises, satisfying `pytest.raises`). So a build **cannot** satisfy both by always-raising — the
asymmetry pin is the real discriminator, exactly as the contract intends (you CAN idempotently REMOVE a
nonexistent membership, but you cannot SET the rank of one).

### Bite 3 — R3 ∀-verb reach pin (w2d, #344/#345) → **CLOSED**
WB: added a new `--keep`-consuming subcommand `archive-keep` to `build_parser`, absent from the coverage
map. `test_the_derived_keep_verb_set_matches_the_ghost_keep_coverage_map`:
```
AssertionError: … derived=['add-household', 'archive-keep', 'remove-household', 'set-rank']
                    mapped=['add-household', 'remove-household', 'set-rank']
1 failed
```
Coverage is a CHECKED variable — the equality reds when the DERIVED parser set grows but the observed
map does not (fails closed on growth). Positive control holds: `create-keep` (which takes `--keeper`,
not `--keep`) is NOT in the derived set.

### Bite 4 — R1 per-type coverage pin (w2c, #344/#345) → **CLOSED**
WB: added a 5th `_KEEP_TYPES` value `workspace` in `surreal_schema.py` with no policy entry.
`test_every_keep_type_has_a_declared_name_policy`:
```
AssertionError: … map=['dm','project','session','team'] vs _KEEP_TYPES=['dm','project','session','team','workspace']
1 failed
```
Positive control — R1's whole rationale, empirically: with the new type present,
`test_create_keep_accepts_every_schema_type` still passes **5 passed** (silently parse-accepting
`workspace`), so WITHOUT R1 the new type's `--name` policy would go unpinned. R1 is the checked
variable that catches the growth.

---

## Inter-pin / new-gap scan (does the assembly hide anything a single-pin view missed?)

- **No collapsing pin pair.** The three interactions I built:
  (1) blocker vs ∀-verb set-rank ghost — both catch the no-op (redundant catchers = strengthening, not
  collapse); they guard DISTINCT paths (real-keep-unruled-rank vs ghost-keep), so neither is deletable:
  a build that exits 1 on a ghost keep but no-ops a real-keep unruled rank passes the ∀-verb pin and
  reds the blocker (bite 1 confirms the blocker fires on exactly that shape).
  (2) ghost-store-pin vs asymmetry-pin — bite 2b proves they discriminate distinct failures.
  (3) ∀-verb ghost pin vs per-`type` reject — orthogonal surfaces (ghost-keep loudness vs name-rule);
  no shared fixture value or branch that could make one vacuous.
- **No wrong build survives the assembled contract.** The revisions only ADD pins, and adding pins
  cannot weaken a contract UNLESS an added pin is vacuous or two contradict — I ruled both out
  (each new pin mutation-proven to bite; satisfiability 92/0). The round-1 base was already cleared
  by adversary-60-w2 (its P1 sweep WB2–WB10); I spot-re-verified 3 of those below.
- **No over-reach.** `_KEEP_VERB_GHOST_KEEP_ARGV` lists exactly the 3 keep-ID verbs (create-keep
  correctly excluded); no pin asserts a listing verb, a `safe_str` on create-keep output, or a DM
  2-member cap (packet 63) — consistent with round 1's "no over-reach" finding.
- **The FR-3-forces-production chain is complete (checked, not assumed).** A new `_KEEP_TYPES` member →
  R1 reds → author adds it to `_NAME_POLICY_BY_TYPE` → the DERIVED `_NAME_REQUIRING_TYPES` (etc.) grows
  → the behavioural per-type test runs for the new type → catches a production `_cmd_create_keep` that
  hand-lists `("project","team")`/`"dm"` and forgot the new type. So the production per-type rule being
  a hand-list is NOT an unguarded reach gap: the derived parametrization makes it a checked variable one
  step downstream. (Production `_cmd_create_keep`'s hand-list is application logic fully covered by the
  8-cell behavioural matrix, not a guard/scan the reach law governs.)
- **`_dispatch_keep` catch-tuple carries every new error class.** `(KeepStoreError,
  SurrealConnectionError, ValueError)` → FR-3 `KeepNotFoundError` (⊂ KeepStoreError), R2 `ValueError`,
  blocker wrapped `KeepStoreError` all laundered to `lore-adm: {error}` + exit 1 — all green in the 92,
  all `err.startswith("lore-adm:")` satisfied.

---

## Spot-checks (round-1 cleared items — still caught against the assembled contract)

WB per line, target pin(s), restored after each:
- **dm-name reject** — `_cmd_create_keep` dm-forbid check removed (creates the keep, prints its id) →
  `test_create_keep_dm_with_a_name_is_rejected` **RED** (1 failed).
- **create-keep-prints-id** — `print(keep.id)` removed →
  `test_create_keep_prints_a_resolvable_keep_id` + `test_the_printed_keep_id_feeds_add_household`
  **both RED** (2 failed).
- **keeper-lockout** — `KeeperLockoutError` guard removed from `keeps.py` →
  store `test_remove_household_REFUSES_to_remove_the_KEEPER` + CLI
  `test_remove_household_refuses_to_remove_the_keeper` **both RED** (2 failed).

---

## P1b — QUANTIFIER TABLE (assembled invariants; round-1 base tables in REPORT-adversary-60-w2 §P1b)

| invariant | classification | receipt |
|---|---|---|
| every keep-ID verb is LOUD (exit 1 + `lore-adm:`) on a ghost keep | **∀-over-the-DERIVED-verb-set** (was GUARDED w/ hole on `remove` in round 1 — R3) | Bite 1 (set-rank ghost reds on no-op), Bite 2a (remove ghost reds when FR-3 dropped); reach = Bite 3. add-household leg is the committed ENFORCED+Q2b path (green in the 92). |
| every WRITE verb is LOUD on a store/domain rejection | **∀-over-the-4-write-verbs** (round-1 hole on set-rank CLOSED) | Bite 1: blocker reds the no-op set-rank; create-keep/add-household/remove-household legs green in the 92 + round-1 sweep. |
| per-`type` `--name` rule holds ∀ type ∈ `_KEEP_TYPES` | **∀ (8 cells) + DERIVED type lists + coverage-checked map** | Bite 4 (R1 coverage reds on a 5th type); 8 behavioural cells all green in the 92; type lists PROJECT from `_NAME_POLICY_BY_TYPE`, no hand-list. |
| project/team missing-name reject TEACHES (names `--name` + the type), exit 1 not 2 | ∀-over-require-types, content+rc checked (R2) | reject pins `[project]`/`[team]` green on the teaching reference; a parser-level (exit 2) or cryptic-message build reds `rc==1`/content (round-1 WB3 + the `rc==1` assertion). |
| remove-of-an-absent-membership on a REAL keep is a BENIGN no-op | ∀ (deliberate asymmetry vs set-rank) | Bite 2b: an always-raise build reds this pin while the ghost pin passes — proven non-collapsing. |

## P1c — REACH TABLE (guards/scans the revisions introduce or rely on)

Legs: **empirical** (in-tree, mutable) for all four new instruments — I added a site / grew the domain
and watched the coverage pin redden.

| instrument | reach DERIVED vs hand-list | coverage a checked variable? | effect vs proxy | verdict |
|---|---|---|---|---|
| `_derive_keep_verbs_taking_keep` + `test_the_derived_keep_verb_set_matches_the_ghost_keep_coverage_map` (w2d) | **DERIVED** — option-string scan of every subparser for `--keep` (production truth) | **YES** — equality reds when the derived set GROWS (Bite 3), fails closed (`assert derived` non-empty) | **effect** (real `build_parser()` introspection) | **SOUND.** Bound (in-docstring): covers verbs spelling the keep arg `--keep`; a `--keep-id`/positional verb escapes — re-open trigger named. |
| `_NAME_POLICY_BY_TYPE` coverage + `test_every_keep_type_has_a_declared_name_policy` (w2c/R1) | **DERIVED** against `_KEEP_TYPES` (schema truth) | **YES** — equality reds when `_KEEP_TYPES` GROWS (Bite 4); second assert pins the value domain | **effect** | **SOUND.** Bound: pins the TEST map coverage; the derived parametrization then forces production coverage of a new type (see §Inter-pin chain). |
| `_derive_keepstore_write_paths` + `test_the_derived_write_path_set_matches_the_coverage_map` (w1, committed) | DERIVED — AST scan of KeepStore write methods | YES (verified at w1) | effect | **RELIED-UPON, SOUND.** The CLI ghost pins depend on the FR-2 Q2b wrap this pin covers; round-1 §P1c verified the wrap via WB10. Unchanged this wave. |
| `test_the_cli_routes_through_build_keep_store` (AST call scan) | hand-checks ONE symbol name is called | n/a (single symbol) | effect (`ast.Call` walk) | **ADEQUATE, non-blocking** (round-1 verdict, unchanged): handlers receive only `(args, keep_store)` — no `config` — so a hand-rolled `KeepStore(...)` at a handler is structurally un-buildable; the reach gap is unreachable through the real entry point. |

No routing-not-sharing / two-source defect: `build_keep_store` is the single construction seam (called
once in the real `_dispatch_keep`); the store rides the shared `_txn` seams (w1's `_query`/write-path
pins prove that by mutation).

## P-PKG

No new mechanism specified by the revisions. The reference reuses `argparse` (parser), the committed
wave-1 `KeepStore` (all store behaviour), and `ast` (test introspection). `Packages considered: none`.

---

## Residuals (each an INDIVIDUAL verdict)

- **R-A (LOW, tighten-if-cheap — NOT a blocker): the dm-reject content check is a loose substring.**
  `test_create_keep_dm_with_a_name_is_rejected` asserts `"dm" in lowered` — and `"dm"` is a substring of
  ordinary words (`admin`, `admissible`), so a dm-reject message that names neither the option-combo nor
  the type but happens to contain such a word would satisfy it. No plausible builder message exploits
  this: any natural teaching message for the dm case names the type `dm` explicitly (the reference does),
  and the companion `"name" in lowered` + `rc==1` + `no keep created` legs already force a real reject.
  I could not construct a natural wrong build that passes on the incidental substring alone. Optional
  hardening (lead's call): assert the type as a whitespace/token match (e.g. `"dm"` in
  `lowered.split()` or `"--type dm" in lowered`). Same check-class round 1 accepted; surfaced per scope
  law, not a gate.
- **R-B (observation, no action): the no-op set-rank is now double-guarded** (blocker + ∀-verb ghost).
  This is strengthening, but worth stating so a future editor does not delete the blocker pin believing
  the ∀-verb pin subsumes it — it does NOT (the ∀-verb pin only exercises the GHOST-keep path; the
  blocker exercises the real-keep unruled-rank path; bite 1 shows a no-op reds both, but a
  real-keep-only-no-op build would red only the blocker). Both must stay.

---

## Instruments (the reference builder, pasted verbatim — brief-base §1)

My only built instrument is `/tmp/pkt60w2b-adv/apply_reference.py` (scratch-only, never the repo tree).
Each wrong build in §Bites/§Spot-checks was a transient in-place edit reversed from a byte-exact
snapshot of the reference (`/tmp/pkt60w2b-ref-backup/{principals,keeps,surreal_schema}.py`); the final
scratch state is the clean reference (byte-exact confirmed).

```python
# apply_reference.py — packet-60 wave-2 REFERENCE build over the scratch copy.
ROOT = Path("/tmp/pkt60w2b-adv/loremaster/loremaster")
PRINCIPALS = ROOT / "principals.py"; KEEPS = ROOT / "keeps.py"

# build_keep_store (mirror build_principal_store, lazy import to dodge the keeps<->principals cycle)
#   raise NotImplementedError(...stub...)  ->
#     from loremaster.keeps import KeepStore
#     return KeepStore(url=config.surreal.url, namespace=config.surreal.namespace,
#         database=config.effective_surreal_database,
#         user=resolve_config_value(config.surreal.user_env),
#         password=resolve_secret(config.surreal.password_env))

# _cmd_create_keep (per-type --name rule + create + print id)
#   raise NotImplementedError(...) ->
#     if args.type in ("project", "team") and args.name is None:
#         raise ValueError(f"--name is required for --type {args.type}")
#     if args.type == "dm" and args.name is not None:
#         raise ValueError(f"--name is not valid for --type {args.type} (a dm keep has no name concept)")
#     keep = await keep_store.create_keep(keeper_email=args.keeper, type=args.type, name=args.name)
#     print(keep.id); return 0

# _cmd_add_household   -> await keep_store.add_household_member(keep_id=args.keep, member_email=args.member); return 0
# _cmd_remove_household-> await keep_store.remove_household_member(keep_id=args.keep, member_email=args.member); return 0
# _cmd_set_rank        -> await keep_store.set_rank(keep_id=args.keep, member_email=args.member, rank=args.rank); return 0

# keeps.py FR-3 amend, in remove_household_member (after the get_keep the lockout guard already does):
#   keep = await self.get_keep(keep_id)
#   if keep is not None and keep.keeper_id == member_id:   ->
#   keep = await self.get_keep(keep_id)
#   if keep is None:
#       raise KeepNotFoundError(f"no keep {keep_id!r} exists — cannot remove a household member from it")
#   if keep.keeper_id == member_id:
```

(Full runnable source with the exactly-once replacement asserts lives at
`/tmp/pkt60w2b-adv/apply_reference.py`; the comment digest above is the reproducible reference so the
claim survives the scratch tree.)

---

## Store-law grounding (cited, `docs/reference/surrealdb-31-capabilities.md`)

- **§2 (DML):** `DELETE … WHERE` of a non-matching row is a no-op → grounds WHY pre-FR-3
  `remove_household_member` was SILENT on a ghost keep (bite 2a reproduced the silence). A missing/unset
  projection reads `None` → `get_keep` returns `None` on a ghost → the FR-3 `if keep is None` fires.
  The explicit `_KEEP_READ_PROJECTION` (never `SELECT *`) is what makes a nameless `dm` keep round-trip
  `name=None` rather than `KeyError` (round-1 attack 9).
- **§4 (GRAPH/RELATE):** `member_of` is `OVERWRITE … ENFORCED` → the ghost-keep RELATE is refused
  (add-household ∀-verb leg); a graph traversal never indexes, so `_read_membership`/`list_household`
  read the edge table as a PLAIN table (the no-match UPDATE readback → `KeepNotFoundError` grounds the
  set-rank ghost leg).
- Error hierarchy: `KeepNotFoundError`/`KeeperLockoutError` ⊂ `KeepStoreError` ⊂ `RuntimeError`, NOT
  `SurrealStoreError` — so both pass through `except SurrealStoreError` untouched and are caught by
  `_dispatch_keep`'s `except KeepStoreError` (exit 1). `SurrealConnectionError`/
  `TxnContentionExhaustedError` ⊂ `SurrealStoreError` re-raise FIRST (the FR-2 Q2b wrap the CLI ghost
  pins lean on — round-1 WB10).

---

## Task / comms / scratch

- Task `ed52981f75f84203920dc871623df4fc` claimed + in_progress (→ done on close).
- Registered on `lore_comms` as `adversary-60-w2b` (session pkt60, role adversary, model
  claude-opus-4-8, cadence ≤30m).
- **Scratch `/tmp/pkt60w2b-adv` + `/tmp/pkt60w2b-ref-backup` left behind** — disposable
  `scripts/scratch_copy.sh` rsync copies in `/tmp` (NOT git worktrees); final state is the clean
  reference build. Reclaim with `./scripts/scratch_copy.sh --force /tmp/pkt60w2b-adv` or an operator
  `rm -rf`. **Cleanup attempted — `rm -rf /tmp/pkt60w2b-adv /tmp/pkt60w2b-ref-backup` was
  guardrail-DENIED** (1 attempt; identical to REPORT-adversary-60-w2 / REPORT-contract-60-w2{c,d}'s
  experience). Flagged so it is not silently abandoned.
